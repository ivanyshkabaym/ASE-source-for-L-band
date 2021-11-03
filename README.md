# ASE-source-for-L-band
In this project, a code was created for the selection and calculation of a cascade for the L-band of a two-stage ASE C+L-band by simulating changes in the output signal depending on the parameters of the input signals and parameters of the doped fiber with using the project tools, that is named pyfiberamp, for calculating fiber-optic amplifiers.
1) Description of the problem
The problem of creating fiber-optic amplifiers and generators based on fibers doped with rare-earth elements using manual experiments has drawbacks. 
For example, in order for the required spectral density at the output from the source, it is necessary to select the optimal fiber length, which must be periodically changed and measured again spectr of output beams. below is a flowchart of the experiment.
![rtAGzHcEQrM](https://user-images.githubusercontent.com/73990802/140079962-9335d106-f3d4-472a-b80d-0b232ade1759.jpg)
To carry out such experiments, equipment for welding, cutting and measuring the spectrum of the output beams is required.
It is possible that designed fiber source or generator can be multistage. In this case, when making changes in one cascade, it may become necessary to make changes in another cascade. 
All this complicates the work, making it monotonous and time-consuming. In addition, the cost of doped fiber per meter can be as high as $ 300 or more.
2) Solution
A good solution is to create software that allows simulating the dependence of the spectral density of the output beam on the parameters of the fiber and input radiation. This gives us the opportunity to speed up and reduce the cost of the development process.
The pyfiberamp project is taken as a basis, which provides calculation tools for creating fiber-optic amplifiers. Link: https://github.com/Jomiri/pyfiberamp.git.
I have created a calculation notebook that allows you to simulate the change in the output beams depending on the geometric parameters, ion concentration, numerical aperture of the nucleus, linear losses, ion lifetime in an excited state and effective absorption and emission cross sections of a doped fiber,
as well as depending on the parameters of the input radiation: power and wavelength of the pump beams, power and wavelength of the beams passing through the cascade.
The main output parameters are: spectral density, the change in signal power depending on the distance traveled in a fiber with given characteristics, which is described at the output by the gain or absorption coefficient.
Two stages in the designed ASE have erbium fibers. Below is a diagram of a two-stage ASE setup, where EDF1 and EDF2 are erbium-doped fibers with different ion densities in the structure. LD1 and LD2 are pump diodes, WDM1 and WDM2 are wavelength division multiplexers, ISO is an optical isolator, OSA is a spectrum analyzer.
![EBXhJEuhGAg](https://user-images.githubusercontent.com/73990802/140104965-3c89f18a-4672-4777-a612-2a08a79632fa.jpg)
To do this, I created files of effective absorption and emission cross sections of erbium, which are replaced in the pyfiberamp project (The project was originally written for ytterbium-doped fibers. I did not change some of the names in the project to "erbium" to avoid conflicts in the program).
In the considered stage for the L-band, Er40-4/125 fiber is used.
In the 'ASE source for Er40' file, you can plot the effective cross sections for the absorption and emission of erbium, the dependence of the amplification or attenuation of the signal on the distance traveled in the erbium fiber, the spectral density of the output signal for forward and backward propagation, and the final output spectral density.
The disadvantages of calculating final output spectral density include low accuracy. This algorithm makes it possible to predict the growth of power, changes in spectral density and, with a certain accuracy, its values with varying fiber length.
In the notebook 'ASE source for Er40', I tried to describe as much information as possible about used parameters and actions performed.
Calculation of final output spectral density helped to save time and avoid unnecessary expenses in my project. 
If you have a questions in this project, please contact me.
