import argparse
import os
import logging as lgg
from math import floor, sqrt
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem


def get_args(argv=None):
    """Parses given arguments and returns argparse.Namespace object."""
    prsr = argparse.ArgumentParser(
        description="Perform a conformational search on given molecules."
    )
    group = prsr.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-m', '--molecules', nargs='+',
        help='One or more files with molecule specification.'
    )
    group.add_argument(
        '-d', '--directory', help='Directory with .mol files.'
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
        '-f', '--fixed', type=int, nargs='+', default=(),
        help='Indices (starting at 1) of atoms fixed during molecule embedding.'
    )
    prsr.add_argument(
        '-x', '--constraints',
        help='File with constraints specified in format '
             '"kind a [b [c [d]] rel min] max [const]", one for line. `kind` '
             'should be one of: P (position), D (distance), A (angle), T '
             '(torsion). Number of required atoms indices depends on `kind` '
             'given and should be 1, 2, 3 or 4 respectively. Atoms indices '
             'start at 1. `rel` should be 0 or 1 and specifies if `min` and '
             '`max` values should be treated as absolute values or relative '
             'to current value. `min` and `max` should be floats, representing '
             'minimum and maximum value of constrained property in relevant '
             'units (angstroms or degrees). `rel` and `min` should be omitted '
             'if `kind` is P. `const` is force constant for given constraint, '
             'should be integer or float, defaults to 1e5.'
    )
    prsr.add_argument(
        '-V', '--verbose', action='store_true',
        help='Sets logging level to INFO.'
    )
    prsr.add_argument(
        '-D', '--debug', action='store_true',
        help='Sets logging level to DEBUG.'
    )
    return prsr.parse_args(argv)


def parse_constraints(params, std_const=1e5):
    """Transforms a string to list of parameters taken by appropriate method
    of ForceField object. String should be in one of the following forms:
        P x min [const]
        D x x rel min max [const]
        A x x x rel min max [const]
        T x x x x rel min max [const]
    where:
    - the first letter defines type of constraint (P = position of atom,
      D = distance between atoms, A = dihedral angle, T = torsion angle),
    - x stands for index of involved atom;
    - `rel` should be 0 or 1 and specifies if `min` and `max` values should be
      treated as absolute values or relative to current value; doesnt apply to P;
    - `min` and `max` represent minimum and maximum value of constrained property
      in relevant units (angstroms or degrees);
    - `const` is force constant for given constraint, if omitted, value of
      `std_const` is used."""
    params = params.split()
    cn = {  # number of coordinates
        'a': 3, 'p': 1, 'd': 2, 't': 4
    }
    kind = params[0].lower()
    atoms, left = params[1:cn[kind] + 1], params[cn[kind] + 1:]
    if kind == 'p':
        other = float(left[0]), (float(left[1]) if len(left) == 2 else std_const)
    else:
        other = bool(left[0]), float(left[1]), float(left[2]), \
                (float(left[3]) if len(left) == 4 else std_const)
    return (kind, *(int(a)-1 for a in atoms), *other)


def get_constraints(file, std_const=1e5):
    """Opens given file and parses it, returning list (one element for line
    in file) of lists of parameters for use in appropriate method of ForceField
    object."""
    with open(file) as f:
        return [parse_constraints(line, std_const) for line in f]


def make_constraints(ff, constraints):
    """Adds specified constraints to given ForceField object, returns that
    object."""
    cm = {  # constraints makers
        'a': ff.MMFFAddAngleConstraint, 'p': ff.MMFFAddPositionConstraint,
        'd': ff.MMFFAddDistanceConstraint, 't': ff.MMFFAddTorsionConstraint
    }
    for kind, *params in constraints:
        cm[kind](*params)
    return ff


def find_lowest_energy_conformer(
        molecule, num_confs, rms_tresh, max_cycles, coord_map, constraints
):
    """Performs a conformational search, keeping track of lowest energy
    conformer.

    Parameters
    ----------
    molecule : rdkit.Mol
        Molecule on which conformational search should be performed.
    num_confs : int
        Number of conformers to generate.
    rms_tresh : float
        Minimum RMS for conformer to be considered different.
    max_cycles : int
        Maximum number of attempts to optimize conformer.
    coord_map : dict
        A mapping of atoms, that should stay in specified positions when
        creating new conformer; key should be an atom index and value should be
        list of cartesian coordinates.
    constraints : list of lists
        List of parameters specifying constraints, if empty list given,
        optimization without any constraints is performed.

    Returns
    -------
    list of [molecule, min_id, min_en, energies], where:
        molecule is molecue with new conformer embedded;
        min_id is id of conformer of lowest energy;
        min_en is energy value of lowest energy conformer;
        energies is a mapping of {id: energy value} for each conformer generated.
    """
    ids = AllChem.EmbedMultipleConfs(
        molecule, numConfs=num_confs, pruneRmsThresh=rms_tresh,
        coordMap=coord_map
    )
    lgg.info("Conformers initialized, starting minimization.")
    min_en, min_id = float('inf'), -1
    energies = {}
    stereo = Chem.FindMolChiralCenters(molecule)
    mp = AllChem.MMFFGetMoleculeProperties(molecule)
    for cid in ids:
        if cid and cid % 100 == 0:
            lgg.info(f"Minimization progress: {cid}/{len(ids)}")
        ff = AllChem.MMFFGetMoleculeForceField(molecule, mp, confId=cid)
        ff.Initialize()
        ff = make_constraints(ff, constraints)
        for cycle in range(max_cycles):
            if not ff.Minimize():
                # ff.Minimize() returns 0 on success
                break
        else:
            molecule.RemoveConformer(cid)
            lgg.debug(f"Conf {cid} ignored: ff.Minimize() unsuccessfull")  
            continue
        energy = ff.CalcEnergy()
        lgg.debug(f"Conf {cid} lowest energy: {energy}")
        energies[cid] = energy
        if energy < min_en:
            lgg.debug(f"Conf {cid} is new min with energy {energy}")
            min_en, min_id = energy, cid
        lgg.debug(
            f"Conf {cid} energy: {energy} kcal/mol"
        )
    lgg.info(
        f"Lowest conformer found: {min_en} kcal/mol"
    )
    return molecule, min_id, min_en, energies
    

def rms_sieve(molecule, energies, threshold):
    """Filters similar conformers after optimization, based on threshold given.
    Always discards conformer of higher energy.

    Parameters
    ----------
    molecule : rdkit.Mol
        Molecule with optimized conformers embedded.
    energies : dict
        mapping of {id: energy value} for each conformer in molecule.
    threshold : float
        Minimum RMS to treat conformers as different.

    Returns
    -------
    rdkit.Mol
        Molecule with conformers filtered."""
    AllChem.AlignMolConformers(molecule)
    indices = {n: c.GetId() for n, c in enumerate(molecule.GetConformers())}
    noh = Chem.RemoveHs(molecule)
    rmsmatrix = AllChem.GetConformerRMSMatrix(noh)
    for i, rms in enumerate(rmsmatrix):
        first = floor((sqrt(8*i+1) - 1) / 2)
        second = indices[i - first * (first + 1) // 2]
        first = indices[first + 1]
        if rms > threshold:
            continue
        try:
            fen = energies[first]
            sen = energies[second]
        except KeyError:
            continue
        throwaway = first if fen > sen else second
        molecule.RemoveConformer(throwaway)
        del energies[throwaway]
        lgg.debug(f"Conf {throwaway} ignored: rms under threshold.")
    return molecule
    
    
def energy_sieve(molecule, energies, threshold):
    """Discards conformers with energies higher than lowest energy + threshold.

    Parameters
    ----------
    molecule : rdkit.Mol
        Molecule with optimized conformers embedded.
    energies : dict
        mapping of {id: energy value} for each conformer in molecule.
    threshold : float
        Maximum energy difference from lowest energy conformer.

    Returns
    -------
    rdkit.Mol
        Molecule with conformers filtered."""
    minen = min(energies.values())
    maxen = minen + threshold
    for cid, en in energies.items():
        if en > maxen:
            molecule.RemoveConformer(cid)
            lgg.debug(
                f"Conf {cid} ignored: energy {en} "
                f"higher than theshold {maxen}"
            )
    return molecule
    
    
def main(argv=None):
    """Performs a conformaional search specified by args given. Run `python
    confsearch.py --help` for details on expected arguments."""
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

    if args.constraints:
        constraints = get_constraints(args.constraints)
    else:
        constraints = {}
    
    os.makedirs(args.output_dir, exist_ok=True)
    report_file = args.output_dir + '\\' + \
        'confsearch_report.txt'
    with open(report_file, 'w') as report:
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
            lgg.debug(f"Stereochemistry found: {Chem.FindMolChiralCenters(m)}")
            
            conf = m.GetConformer()
            coord_map = {n-1: conf.GetAtomPosition(n-1) for n in args.fixed}
            
            m, cid, en, ens = find_lowest_energy_conformer(
                m, args.num_confs, args.rms_tresh, args.max_cycles, coord_map,
                constraints
            )
            num = m.GetNumConformers()
            lgg.info(f"Number of conformers optimized: {num}")
            m = energy_sieve(m, ens, args.energy_window)
            lgg.info(
                f"{num-m.GetNumConformers()} conformers outside energy window."
            )
            num = m.GetNumConformers()
            m = rms_sieve(m, ens, args.rms_tresh)
            lgg.info(
                f"{num-m.GetNumConformers()} conformers discarded by "
                "RMS sieve."
            )
            lgg.info(f"Number of conformers generated: {m.GetNumConformers()}")
            molrepr = Chem.MolToMolBlock(m, confId=cid)
            molfilename = mol.split('\\')[-1]
            outfile = args.output_dir + '\\' + molfilename.split('.')[-2] \
                + '_min_conf.mol'
            with open(outfile, 'w') as file:
                file.write(molrepr)
            lgg.info(f"Lowest energy conformer saved to {outfile}")
            report.write(
                f"{name: <{longest}} = {en: > 13.8f} kcal/mol\n"
            )
            sdfile = args.output_dir + '\\' + molfilename.split('.')[-2] \
                + '_confs.sdf'
            writer = Chem.SDWriter(sdfile)
            for conf in m.GetConformers():
                writer.write(m, confId=conf.GetId())
            writer.close()
    
    
if __name__ == '__main__':

    main()
