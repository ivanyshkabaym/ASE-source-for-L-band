import matplotlib.pyplot as plt

from pyfiberamp.util.sliced_array import SlicedArray
from pyfiberamp.helper_funcs import *
from pyfiberamp.fibers import PassiveFiber

class SimulationResult:
    def __init__(self, z, powers, upper_level_fraction, channels, fiber, backward_raman_allowed=True):
        self.z = z
        slices = channels.get_slices()
        self.channels = channels
        self.labels = channels.get_labels()
        self.powers = SlicedArray(powers, slices)
        self.wavelengths = channels.get_wavelengths()
        self.upper_level_fraction = upper_level_fraction
        self._backward_raman_allowed = backward_raman_allowed
        self.fiber = fiber
        self.use_db_scale = False

    @property
    def local_average_excitation(self):
        weights = self.fiber.doping_profile.areas
        norm_weights = weights[:, np.newaxis] / sum(weights) * len(weights)
        return np.mean(self.upper_level_fraction * norm_weights, axis=0)

    @property
    def overall_average_excitation(self):
        return np.mean(self.local_average_excitation)

    def make_result_dict(self):
        result_dict = {}
        for key in CHANNEL_TYPES:
            power = getattr(self.powers, key)
            if len(power) == 0:
                continue
            start_idx, end_idx = self.start_and_end_idx_from_channel_type(key)
            output_powers = power[:, end_idx]
            input_powers = power[:, start_idx]
            gain = to_db(output_powers / input_powers)
            result_dict[key] = {'input_powers': input_powers,
                                'output_powers': output_powers,
                                'gain': gain}
        return result_dict

    def powers_at_fiber_end(self):
        forward_slice, backward_slice = self.channels.get_forward_and_backward_slices()
        return np.hstack((self.powers[forward_slice,-1], self.powers[backward_slice,0]))

    def start_and_end_idx_from_channel_type(self, channel_type):
        return (0, -1) if 'forward' in channel_type else (-1, 0)

    def plot_amplifier_result(self):
        self.plot_power_evolution()
        self.plot_ase_spectra()
        plt.show()

    def plot_power_evolution(self):
        fig, ax = plt.subplots()
        for ch in CHANNEL_TYPES:
            self.plot_single_channel_type_power_evolution(ax, ch)
        self.finalize_fiber_power_plot(ax)

        ax_right = ax.twinx()
        self.plot_excited_ion_fraction(ax_right)
        self.make_power_evolution_legend(ax, ax_right)
        plt.show()

    def plot_single_channel_type_power_evolution(self, ax, channel_type):
        if 'forward_ase' in channel_type:
            self.plot_ase_evolution(ax)
        elif 'backward_ase' in channel_type: # We don't want to plot ase twice
            return
        else:
            self.plot_normal_channel_power_evolution(ax, channel_type)

    def plot_ase_evolution(self, ax):
        if len(self.wavelengths.forward_ase) != 0:
            forward_ase = np.sum(self.powers.forward_ase, axis=0)
            forward_ase_power = forward_ase[-1]
            ax.plot(self.z, self.plotting_transformation(forward_ase),
                    label='Forward ASE, power={:.2f} mW'.format(forward_ase_power * 1000))

            backward_ase = np.sum(self.powers.backward_ase, axis=0)
            backward_ase_power = backward_ase[0]
            ax.plot(self.z, self.plotting_transformation(backward_ase),
                    label='Backward ASE, power={:.2f} mW'.format(backward_ase_power * 1000))

    def plot_normal_channel_power_evolution(self, ax, channel_type):
        wls = getattr(self.wavelengths, channel_type)
        channel_powers = getattr(self.powers, channel_type)
        for i in range(len(wls)):
            self.plot_single_channel(ax, wls[i], channel_powers[i, :], channel_type)

    def plot_single_channel(self, ax, wl, single_channel_power, channel_type):
        start_idx, end_idx = self.start_and_end_idx_from_channel_type(channel_type)
        input_power = single_channel_power[start_idx]
        output_power = single_channel_power[end_idx]
        gain_or_absorption = to_db(output_power / input_power)
        ax.plot(self.z, self.plotting_transformation(single_channel_power),
                label=self.make_legend_entry(channel_type, wl, gain_or_absorption, output_power))

    def make_legend_entry(self, channel_type, wl, gain_or_absorption, output_power):
        label_start = '{ch_type}, {wl:.1f} nm, '.format(ch_type=self.channel_type_to_title(channel_type), wl=wl * 1e9)
        power_label = self.make_power_label(output_power)
        db_label = self.make_db_label(gain_or_absorption, channel_type)
        return label_start + power_label + db_label

    def make_power_label(self, output_power):
        if self.use_db_scale:
            power, unit = (to_dbm(output_power), 'dBm')
        else:
            use_watts = output_power > 1
            power, unit = (output_power, 'W') if use_watts else (output_power*1000, 'mW')
        return 'output={power:.1f} {unit}, '.format(power=power, unit=unit)

    def make_db_label(self, gain_or_absorption, channel_type):
        include_db = 'pump' in channel_type or 'signal' in channel_type
        if not include_db:
            return ''
        gain_label = 'gain' if gain_or_absorption > 0 else 'absorption'
        return '{g_or_a}={db_value:.1f} dB'.format(g_or_a=gain_label, db_value=abs(gain_or_absorption))

    def channel_type_to_title(self, channel_type):
        return channel_type.replace('_', ' ').title()

    @staticmethod
    def make_power_evolution_legend(ax, ax_right):
        ion_line, ion_label = ax_right.get_legend_handles_labels()
        power_lines, power_labels = ax.get_legend_handles_labels()
        ax.legend(power_lines + ion_line, power_labels + ion_label)

    def finalize_fiber_power_plot(self, ax):
        x_label = 'Z (m)'
        y_label = 'Power ({unit})'.format(unit=self.power_evolution_unit())
        xlim = [self.z[0], self.z[-1]]
        self.finalize_power_plot(ax, x_label, y_label, xlim)

    def finalize_power_plot(self, ax, x_label, y_label, xlim):
        ax.tick_params(which='minor', direction='in', left=True, right=False, top=True, bottom=False,
                       width=2, length=6)
        ax.tick_params(which='major', direction='in', left=True, right=False, top=True, bottom=True,
                       width=3, length=10, labelsize=16)
        ax.set_xlabel(x_label, fontsize=18)
        ax.set_ylabel(y_label, fontsize=18)
        ax.set_xlim(xlim)
        if not self.use_db_scale:
            ax.set_ylim([0, ax.get_ylim()[1]])
        ax.grid(True)

    def plot_excited_ion_fraction(self, ax):
        if isinstance(self.fiber, PassiveFiber):
            ax.set_axis_off()
            return
        ax.plot(self.z, self.local_average_excitation * 100, '--', label='Excited ion fraction')
        ax.set_ylabel('Ions at the upper laser level (%)', fontsize=18)
        ax.yaxis.set_ticks_position('right')
        ax.tick_params(which='major', direction='in', left=False, right=True, top=True, bottom=True,
                       width=3, length=10, labelsize=16)
        ax.set_xlim([self.z[0], self.z[-1]])
        ax.set_ylim([0, 100])

    def plot_ase_spectra(self):
        if len(self.wavelengths.forward_ase) == 0:
            return
        fig, ax = plt.subplots()
        forward_ase_spectrum = self.powers.forward_ase[:, -1]
        backward_ase_spectrum = self.powers.backward_ase[:, 0]
        ase_wls_nm = self.wavelengths.forward_ase * 1e9
        ase_wl_step = ase_wls_nm[1] - ase_wls_nm[0]
        ax.plot(ase_wls_nm, to_dbm(forward_ase_spectrum / ase_wl_step), label='Forward ASE')
        ax.plot(ase_wls_nm, to_dbm(backward_ase_spectrum / ase_wl_step), label='Backward ASE')
        ax.set_xlabel('Wavelength (nm)', fontsize=18)
        ax.set_ylabel('Power spectral density (dBm/nm)', fontsize=18)
        ax.set_xlim([ase_wls_nm[0], ase_wls_nm[-1]])
        ax.tick_params(which='major', direction='in', left=True, right=True, top=True, bottom=True,
                       width=3, length=10, labelsize=16)
        ax.legend()
        plt.show()

    def plot_signal_intensity(self, effective_area):
        intensity = self.powers.forward_signal[0, :] / effective_area
        plt.plot(self.z, intensity)
        plt.show()

    def plot_total_power(self):
        fig, ax = plt.subplots()
        total_power = np.sum(self.powers, axis=0)
        ax.plot(self.z, total_power, label='Total power in fiber')
        ax.set_xlabel('Z (m)', fontsize=18)
        ax.set_ylabel('Total power in fiber (W)', fontsize=18)
        ax.set_ylim([0, ax.get_ylim()[1]])

    def power_evolution_unit(self):
        return 'dBm' if self.use_db_scale else 'W'

    def plotting_transformation(self, power):
        return to_db(power * 1000) if self.use_db_scale else power

    def plot_transverse_ion_excitation(self):
        assert self.fiber.doping_profile.radii is not None, 'Doping profile radii not defined.'
        assert self.fiber.num_ion_populations > 1, 'More than one ion population needed for transverse plotting.'
        from mpl_toolkits.mplot3d import Axes3D
        from matplotlib import cm

        radii = self.fiber.doping_profile.radii
        n2 = self.upper_level_fraction
        n2_plot = np.vstack((n2[::-1,:], n2))
        max_r = radii[-1]
        r_plot = np.linspace(-max_r, max_r, len(radii) * 2)[:, np.newaxis] * np.ones(n2_plot.shape[1])[np.newaxis, :]
        l_plot = self.z[np.newaxis, :] * np.ones(n2_plot.shape[0])[:, np.newaxis]

        #plt.imshow(n2_plot, extent=(-max_r, max_r, 0, self.fiber.length))
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        ax.plot_surface(l_plot, r_plot*1e6, n2_plot, cmap=cm.coolwarm)
        ax.set_xlabel('Distance (m)', fontsize=18)
        ax.set_ylabel('Radius (um)', fontsize=18)
        ax.set_zlabel('Fractional excitation', fontsize=18)
        plt.show()


