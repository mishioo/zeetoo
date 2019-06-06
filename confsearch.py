import argparse
import csv
import os
import time
import logging as lgg
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem


def conf_search(mol, num=100):
    confs = []
    for __ in range(num):
        cid = AllChem.EmbedMolecule(mol, clearConfs=False)
        mp = AllChem.MMFFGetMoleculeProperties(mol)
        ff = AllChem.MMFFGetMoleculeForceField(mol, mp, confId=cid)
        ff.Initialize()
        min_out = ff.Minimize()
        confs.append((cid, ff.CalcEnergy(), min_out))
        lgg.info(f'Search progress: {cid}/{num}')
    return sorted(confs, key=lambda x: x[1])
    
    
def get_args(argv=None):
    prsr = argparse.ArgumentParser(
        description="Perform a conformational search on given molecules."
    )
    group = prsr.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-m', '--molecules', nargs='+',
        help='One or more files with molecule specification.'
    )
    group.add_argument(
        '-d', '--directory',
        help='Directory with .mol files.'
    )
    prsr.add_argument(
        '-o', '--output_dir', default='.\\confsearch', help='Output directory.'
    )
    prsr.add_argument(
        '-n', '--num_confs', type=int, default=10,
        help='Number of cnformers to generate.'
    )
    prsr.add_argument(
        '-r', '--rms_tresh', type=float, default=1,
        help='Maximum RMSD of conformers.'
    )
    prsr.add_argument(
        '-e', '--energy_window', type=float, default=5,
        help='Maximum energy difference from lowest-energy conformer '
        'in kcal/mol.'
    )
    prsr.add_argument(
        '-c', '--max_cycles', type=int, default=10,
        help='Maximum number of energy minimization cycles.'
    )
    prsr.add_argument(
        '-v', '--verbose', action='store_true'
    )
    prsr.add_argument(
        '-D', '--debug', action='store_true'
    )
    return prsr.parse_args(argv)
    
    
def find_lowest_energy_conformer(
        molecule, num_confs, rms_tresh, energy_window, max_cycles
):
    ids = AllChem.EmbedMultipleConfs(
        molecule, numConfs=num_confs, pruneRmsThresh=rms_tresh
    )
    lgg.info("Conformers initialized, starting minimization.")
    min_en, min_id = float('inf'), -1
    stereo = Chem.FindMolChiralCenters(molecule)
    mp = AllChem.MMFFGetMoleculeProperties(molecule)
    for cid in ids:
        if cid and cid % 100 == 0:
            lgg.info(f"Minimization progress: {cid}/{len(ids)}")
        ff = AllChem.MMFFGetMoleculeForceField(molecule, mp, confId=cid)
        ff.Initialize()
        for cycle in range(max_cycles):
            if not ff.Minimize():
                # ff.Minimize() returns 0 on success
                lgg.debug(f"Conf {cid} minimized on cycle {cycle + 1}.")
                break
        else:
            lgg.debug(f"Conf {cid} ignored: ff.Minimize() unsuccessfull")  
            continue
        Chem.AssignStereochemistryFrom3D(molecule, confId=cid)
        if stereo != Chem.FindMolChiralCenters(molecule):
            lgg.debug(f"Conf {cid} ignored: stereochemistry violation.")
            continue
        energy = ff.CalcEnergy()
        if energy > min_en + energy_window:
            lgg.debug(
                f"Conf {cid} ignored: energy {energy} "
                f"higher than {min_en + energy_window}"
            )
            continue
        lgg.debug(f"Conf {cid} lowest energy: {energy}")
        # rms =  AllChem.GetConformerRMS(molecule, cid, min_id)
        # if rms_tresh > rms:
            # lgg.debug(f"conf {cid} ignored: rmsd higher than threshhold: {rms}")
            # continue
        if energy < min_en:
            lgg.debug(f"Conf {cid} is new min with energy {energy}")
            min_en, min_id = energy, cid
        lgg.debug(
            f"Conf {cid} energy: {energy} kcal/mol"
        )
    lgg.info(
        f"Lowest conformer found: {min_en} kcal/mol"
    )
    return molecule, min_id, min_en
    
    
def main(argv=None):
    args = get_args(argv)
    if args.verbose:
        level = lgg.INFO
    elif args.debug:
        level = lgg.DEBUG
    else:
        level = lgg.WARNING
    lgg.basicConfig(level=level)
    lgg.info(f"Confsearch by Michał M. Więcław")
    
    if args.molecules is None:
        mol_names = [name for name in os.listdir(args.directory)
                     if name.endswith('.mol')]
        molecules = [args.directory + '\\' + name for name in mol_names]
    else:
        molecules = args.molecules
        mol_names = [mol.split('\\')[-1] for mol in molecules]
    lgg.debug(f"molecules: {molecules}")
    lgg.debug(f"molecules names: {mol_names}")
    
    os.makedirs(args.output_dir, exist_ok=True)
    report_file = args.output_dir + '\\' + \
        f'confsearch_report_{int(time.time())}.txt'
    with open(report_file, 'a') as report:
        report.write(
            f"Confsearch -- RMSD treshold   = {args.rms_tresh} Anstrom,\n"
            f"              energy window   = {args.energy_window} kcal/mol,\n"
            f"              confs requested = {args.num_confs}\n\n"
        )
        report.write(f"Energies values of most stable conformers:\n")
        longest = max(map(len, mol_names))
        for mol, name in zip(molecules, mol_names):
            lgg.info(f"Starting with molecule {name}")
            m = Chem.MolFromMolFile(mol, removeHs=False)
            if m is not None:
                lgg.info('Molecule loaded.')
            else:
                lgg.warning(f"Couldn't load molecule {name}")
                continue
                
            atoms = {}
            for atnum in (atom.GetAtomicNum() for atom in m.GetAtoms()):
                atoms[atnum] = atoms.get(atnum, 0) + 1
            lgg.debug(f"atoms in structure: {atoms}")
            Chem.AssignStereochemistryFrom3D(m)
            lgg.info(f"Stereochemistry found: {Chem.FindMolChiralCenters(m)}")
            
            m, cid, en = find_lowest_energy_conformer(
                m, args.num_confs, args.rms_tresh, args.energy_window,
                args.max_cycles
            )
            molrepr = Chem.MolToMolBlock(m, confId=cid)
            outfile = mol.split('.')
            outfile = args.output_dir + '\\' + outfile[-2] + '_min_conf.mol'
            with open(outfile, 'w') as file:
                file.write(molrepr)
            lgg.info(f"Lowest energy conformer saved to {outfile}")
            report.write(
                f"{name: <{longest}} = {en: > 13.8f} kcal/mol\n"
            )
    
    
if __name__ == '__main__':

    main()

    # if len(sys.argv) == 2:
        # num_conf = int(sys.argv[1])
    # else:
        # num_conf = 10
    # mol = Chem.AddHs(Chem.MolFromMolFile(r'D:\Obliczenia\AU-GalCy\AU-GalCy.mol'))
    # lgg.info("Molecule loaded, initializing search.")
    # confs = conf_search(mol, num_conf)
    # best = confs[0][0]
    # kept = 1
    # with open(r'D:\Obliczenia\AU-GalCy\list.txt', 'w', newline='') as lsfile:
        # lswriter = csv.writer(lsfile, delimiter='\t')
        # cfwriter = AllChem.SDWriter(r'D:\Obliczenia\AU-GalCy\conformers.sdf')
        # for cid, en, min_out in confs:
            # rms = AllChem.GetConformerRMS(mol, best, cid, prealigned=True)
            # if rms > 0.1: kept += 1
            # lswriter.writerow((cid, en, min_out, rms))
            # cfwriter.write(mol, confId=cid)
    # lgg.info(f'RMS calculated, kpet = {kept}')
