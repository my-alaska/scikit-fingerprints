from typing import Union

import e3fp.fingerprint.fprint
from e3fp.conformer.generate import (
    NUM_CONF_DEF,
    POOL_MULTIPLIER_DEF,
    RMSD_CUTOFF_DEF,
    MAX_ENERGY_DIFF_DEF,
    FORCEFIELD_DEF,
    SEED_DEF,
)
import numpy as np
import pandas as pd
from rdkit.Chem import MolToSmiles

from base import FingerprintTransformer

"""
If during multiprocessing occurs MaybeEncodingError, first check if there isn't thrown any exception inside
worker function! (That error isn't very informative and this tip might save you a lot of time)
"""

"""
fp_descriptors needs to be here or inside _transform() of a specific class (cannot be defined inside the __init__() of
that class), otherwise pickle gets angry:
        TypeError: cannot pickle 'Boost.Python.function' object
"""


class MorganFingerprint(FingerprintTransformer):
    def __init__(
        self,
        radius: int = 2,
        n_bits: int = 2048,
        use_chirality: bool = False,
        use_bond_types: bool = True,
        use_features: bool = False,
        sparse: bool = False,
        result_type: str = "default",
        n_jobs: int = 1,
        verbose: int = 0,
    ):
        assert result_type in ["default", "as_bit_vect", "hashed"]

        super().__init__(n_jobs, verbose)
        self.radius = radius
        self.n_bits = n_bits
        self.use_chirality = use_chirality
        self.use_bond_types = use_bond_types
        self.use_features = use_features
        self.result_type = result_type

    def _calculate_fingerprint(
        self, X: Union[pd.DataFrame, np.ndarray]
    ) -> np.ndarray:
        if self.result_type == "default":
            from rdkit.Chem.rdMolDescriptors import GetMorganFingerprint

            return np.array(
                [
                    GetMorganFingerprint(
                        x,
                        radius=self.radius,
                        useChirality=self.use_chirality,
                        useBondTypes=self.use_bond_types,
                        useFeatures=self.use_features,
                    )
                    for x in X
                ]
            )
        elif self.result_type == "as_bit_vect":
            from rdkit.Chem.rdMolDescriptors import (
                GetMorganFingerprintAsBitVect,
            )

            return np.array(
                [
                    GetMorganFingerprintAsBitVect(
                        x,
                        radius=self.radius,
                        useChirality=self.use_chirality,
                        useBondTypes=self.use_bond_types,
                        useFeatures=self.use_features,
                        nBits=self.n_bits,
                    )
                    for x in X
                ]
            )
        else:
            from rdkit.Chem.rdMolDescriptors import GetHashedMorganFingerprint

            return np.array(
                [
                    GetHashedMorganFingerprint(
                        x,
                        radius=self.radius,
                        useChirality=self.use_chirality,
                        useBondTypes=self.use_bond_types,
                        useFeatures=self.use_features,
                        nBits=self.n_bits,
                    )
                    for x in X
                ]
            )


class MACCSKeysFingerprint(FingerprintTransformer):
    def __init__(
        self, sparse: bool = False, n_jobs: int = 1, verbose: int = 0
    ):  # the sparse parameter will be unused
        super().__init__(n_jobs, verbose)

    def _calculate_fingerprint(
        self, X: Union[pd.DataFrame, np.ndarray]
    ) -> np.ndarray:
        from rdkit.Chem.rdMolDescriptors import GetMACCSKeysFingerprint

        return np.array([GetMACCSKeysFingerprint(x) for x in X])


class AtomPairFingerprint(FingerprintTransformer):
    def __init__(
        self,
        n_bits: int = 2048,
        min_length: int = 1,
        max_length: int = 30,
        from_atoms: int = 0,
        ignore_atoms: int = 0,
        atom_invariants: int = 0,
        n_bits_per_entry: int = 4,
        include_chirality: bool = False,
        use_2D: bool = True,
        sparse: bool = False,
        result_type: str = "default",
        n_jobs: int = 1,
        verbose: int = 0,
    ):
        assert result_type in ["default", "as_bit_vect", "hashed"]

        super().__init__(n_jobs, verbose)
        self.n_bits = n_bits
        self.min_length = min_length
        self.max_length = max_length
        self.from_atoms = from_atoms
        self.ignore_atoms = ignore_atoms
        self.atom_invariants = atom_invariants
        self.n_bits_per_entry = n_bits_per_entry
        self.include_chirality = include_chirality
        self.use_2D = use_2D
        self.result_type = result_type

    def _calculate_fingerprint(
        self, X: Union[pd.DataFrame, np.ndarray]
    ) -> np.ndarray:
        fp_args = {
            "minLength": self.min_length,
            "maxLength": self.max_length,
            "fromAtoms": self.from_atoms,
            "ignoreAtoms": self.ignore_atoms,
            "atomInvariants": self.atom_invariants,
            "includeChirality": self.include_chirality,
            "use2D": self.use_2D,
        }

        if self.result_type == "default":
            from rdkit.Chem.rdMolDescriptors import GetAtomPairFingerprint

            fp_function = GetAtomPairFingerprint
        elif self.result_type == "as_bit_vect":
            from rdkit.Chem.rdMolDescriptors import (
                GetHashedAtomPairFingerprintAsBitVect,
            )

            fp_function = GetHashedAtomPairFingerprintAsBitVect
            fp_args["nBits"] = self.n_bits
            fp_args["nBitsPerEntry"] = self.n_bits_per_entry
        else:
            from rdkit.Chem.rdMolDescriptors import (
                GetHashedAtomPairFingerprint,
            )

            fp_function = GetHashedAtomPairFingerprint
            fp_args["nBits"] = self.n_bits

        return np.array([fp_function(x, **fp_args) for x in X])


class TopologicalTorsionFingerprint(FingerprintTransformer):
    def __init__(
        self,
        n_bits: int = 2048,
        target_size: int = 4,
        from_atoms: int = 0,
        ignore_atoms: int = 0,
        atom_invariants: int = 0,
        include_chirality: bool = False,
        sparse: bool = False,
        result_type: str = "default",
        n_jobs: int = 1,
        verbose: int = 0,
    ):
        assert result_type in ["default", "as_bit_vect", "hashed"]

        super().__init__(n_jobs, verbose)
        self.n_bits = n_bits
        self.target_size = target_size
        self.from_atoms = from_atoms
        self.ignore_atoms = ignore_atoms
        self.atom_invariants = atom_invariants
        self.include_chirality = include_chirality
        self.result_type = result_type

    def _calculate_fingerprint(
        self, X: Union[pd.DataFrame, np.ndarray]
    ) -> np.ndarray:
        fp_args = {
            "targetSize": self.target_size,
            "fromAtoms": self.from_atoms,
            "ignoreAtoms": self.ignore_atoms,
            "atomInvariants": self.atom_invariants,
            "includeChirality": self.include_chirality,
        }

        if self.result_type == "default":
            from rdkit.Chem.rdMolDescriptors import (
                GetTopologicalTorsionFingerprint,
            )

            fp_function = GetTopologicalTorsionFingerprint
        elif self.result_type == "as_bit_vect":
            from rdkit.Chem.rdMolDescriptors import (
                GetHashedTopologicalTorsionFingerprintAsBitVect,
            )

            fp_function = GetHashedTopologicalTorsionFingerprintAsBitVect
            fp_args["nBits"] = self.n_bits
        else:
            from rdkit.Chem.rdMolDescriptors import (
                GetHashedTopologicalTorsionFingerprint,
            )

            fp_function = GetHashedTopologicalTorsionFingerprint
            fp_args["nBits"] = self.n_bits

        return np.array([fp_function(x, **fp_args) for x in X])


class ERGFingerprint(FingerprintTransformer):
    def __init__(
        self,
        atom_types: int = 0,
        fuzz_increment: float = 0.3,
        min_path: int = 1,
        max_path: int = 15,
        sparse: bool = False,
        n_jobs: int = 1,
        verbose: int = 0,
    ):
        super().__init__(n_jobs, verbose)
        self.atom_types = atom_types
        self.fuzz_increment = fuzz_increment
        self.min_path = min_path
        self.max_path = max_path

    def _calculate_fingerprint(
        self, X: Union[pd.DataFrame, np.ndarray]
    ) -> np.ndarray:
        from rdkit.Chem.rdReducedGraphs import GetErGFingerprint

        fp_args = {
            "atomTypes": self.atom_types,
            "fuzzIncrement": self.fuzz_increment,
            "minPath": self.min_path,
            "maxPath": self.max_path,
        }

        return np.array([GetErGFingerprint(x, **fp_args) for x in X])


class E3FP(FingerprintTransformer):
    def __init__(
        self,
        bits: int,
        radius_multiplier: float,
        rdkit_invariants: bool = True,
        first: int = 1,
        num_conf: int = NUM_CONF_DEF,
        pool_multiplier: float = POOL_MULTIPLIER_DEF,
        rmsd_cutoff: float = RMSD_CUTOFF_DEF,
        max_energy_diff: float = MAX_ENERGY_DIFF_DEF,
        force_field: float = FORCEFIELD_DEF,
        get_values: bool = True,
        is_folded: bool = False,
        fold_bits: int = 1024,
        standardise: bool = True,
        random_state: int = 0,
        n_jobs: int = 1,
        verbose: int = 0,
    ):
        super().__init__(n_jobs, verbose)
        self.bits = bits
        self.radius_multiplier = radius_multiplier
        self.rdkit_invariants = rdkit_invariants
        self.first = first
        self.num_conf = num_conf
        self.pool_multiplier = pool_multiplier
        self.rmsd_cutoff = rmsd_cutoff
        self.max_energy_diff = max_energy_diff
        self.force_field = force_field
        self.get_values = get_values
        self.is_folded = is_folded
        self.fold_bits = fold_bits
        self.standardise = standardise
        self.random_state = random_state

    def _calculate_fingerprint(
        self, X: Union[pd.DataFrame, np.ndarray]
    ) -> np.ndarray:
        from e3fp.conformer.util import mol_from_smiles
        from e3fp.conformer.generator import ConformerGenerator
        from e3fp.pipeline import fprints_from_mol

        conf_gen = ConformerGenerator(
            first=self.first,
            num_conf=self.num_conf,
            pool_multiplier=self.pool_multiplier,
            rmsd_cutoff=self.rmsd_cutoff,
            max_energy_diff=self.max_energy_diff,
            forcefield=self.force_field,
            get_values=self.get_values,
            seed=self.random_state,
        )

        result = []

        for x in X:
            input_mol = mol_from_smiles(
                smiles=MolToSmiles(x),
                name=MolToSmiles(x),
                standardise=self.standardise,
            )

            # Generating conformers. Only few first conformers with lowest energy are used - specified by self.first
            mol, values = conf_gen.generate_conformers(input_mol)

            max_conformers, indices, energies, rmsds_mat = values

            fps = fprints_from_mol(
                mol,
                fprint_params={
                    "bits": self.bits,
                    "radius_multiplier": self.radius_multiplier,
                    "rdkit_invariants": self.rdkit_invariants,
                },
            )

            # Set a property for each fingerprint, to be able to obtain energy later
            for i in range(len(fps)):
                fps[i].set_prop("Energy", energies[i])

                if self.is_folded:
                    fps[i] = fps[i].fold(self.fold_bits)

            result.extend(fps)

        result = np.array(result)

        return result
