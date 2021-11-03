import numpy as np
from pyfiberamp.dynamic.dynamic_solver_python import DynamicSolverPython
from pyfiberamp.parameters import SIMULATION_MIN_POWER
from pyfiberamp.dynamic import fiber_simulation_pythran_bindings as bindings


class DynamicSolverPythran(DynamicSolverPython):
    def _bfecc_simulation(self, P_fiber_in, N2_in, dPdz, dN2dt,
                          boundary_conditions, convergence_checker, dz, dt, n_forward):
        P = np.zeros((P_fiber_in.shape[0], P_fiber_in.shape[1] + 1))
        P_hat_forward = np.zeros_like(P)
        P_hat_backward = np.zeros_like(P)
        P[:, :-1] = P_fiber_in
        P[:, -1] = P_fiber_in[:, -1]

        N2 = np.zeros((N2_in.shape[0], N2_in.shape[1] + 1))
        N2[:, :-1] = N2_in
        N2[:, -1] = N2_in[:, -1]

        # Unpack class attributes.
        source_idx = np.array([i[0] for i in boundary_conditions.reflections], dtype=np.int)
        target_idx = np.array([i[1] for i in boundary_conditions.reflections], dtype=np.int)
        R = np.array([i[2] for i in boundary_conditions.reflections], dtype=np.float)
        P_in_out = boundary_conditions.P_in_out
        num_ion_populations = dN2dt.num_ion_populations
        n_channels = dN2dt.n_channels
        a_per_h_v_pi_r2 = dN2dt.a_per_h_v_pi_r2
        a_g_per_h_v_pi_r2_Nt = dN2dt.a_g_per_h_v_pi_r2_Nt
        A = dN2dt.A
        a_g_per_Nt = dPdz.a_g_per_Nt
        a_l = dPdz.a_l
        g_m_h_v_dv_per_Nt = dPdz.g_m_h_v_dv_per_Nt

        idx_iteration = 0
        while convergence_checker.has_not_converged(N2, idx_iteration):
            # The first array argument passed to each of these binding
            # functions is modified in-place.
            bindings.apply_input(P, P_in_out, idx_iteration, n_forward)
            bindings.apply_reflection(P, source_idx, target_idx, R, n_forward)
            bindings.dNdT(N2, P, a_per_h_v_pi_r2, a_g_per_h_v_pi_r2_Nt, A, dt, num_ion_populations, n_channels)
            bindings.min_clamp(N2, SIMULATION_MIN_POWER)
            bindings.shift_to_propagation_direction_to_from(P_hat_forward, P, n_forward)
            bindings.apply_output(P_in_out, P_hat_forward, idx_iteration, n_forward)
            bindings.dPdZ(P_hat_forward, N2, a_g_per_Nt, a_l, g_m_h_v_dv_per_Nt, dz, num_ion_populations, n_channels, True)
            bindings.min_clamp(P_hat_forward, SIMULATION_MIN_POWER)
            bindings.shift_against_propagation_direction_to_from(P_hat_backward, P_hat_forward, n_forward)
            bindings.dPdZ(P_hat_backward, N2, a_g_per_Nt, a_l, g_m_h_v_dv_per_Nt, dz, num_ion_populations, n_channels, False)
            bindings.new_P(P, P_hat_forward, P_hat_backward)
            bindings.min_clamp(P, SIMULATION_MIN_POWER)
            idx_iteration += 1

        boundary_conditions.apply_input(P, idx_iteration)
        boundary_conditions.apply_reflection(P)
        boundary_conditions.correct_output_by_reflection()
        return P, N2, idx_iteration
