from utils import *
from servos import *
from sdrs import *
from servos_sdrs import *
from map_probability import *

num_antennas = 3
fc = 910e6 # 910e6 # 145.6e6
antennas = [0]

grid_size = 40
locs = np.array([[20, 20], [10, 10], [10, 15]])
orientations = np.array([-np.pi/2., -np.pi/2., 0])

##########################
# Create servos and sdrs #
##########################
servos = Servos(num_antennas, '/dev/ttyACM0')

dev_cnt = librtlsdr.rtlsdr_get_device_count()
rtlsdr_devs = [i if i < dev_cnt else None for i in xrange(num_antennas)]
sdrs = SDRs(rtlsdr_devs, fc)

servos_sdrs = ServosSDRs(servos, sdrs)

map_prob = MapProbability(locs, orientations, grid_size)


###################
# Initializations #
###################
sdrs.set_gains(1e6)

###################################
# Continuously plot incoming data #
###################################

prob_updated = [False]*num_antennas

def plot_step(ith):
    angles_and_maxpowers = servos_sdrs.get_angles_and_maxpowers(ith)
    if angles_and_maxpowers is not None:
        print('# {0} received #'.format(ith))
        angles, mp = angles_and_maxpowers
        
        angles = angles[::-1] # TODO: might be different for different servos
        mp_med = signal.medfilt(mp, 3)
        mp_smooth = smoothMaxPower(mp, 20)
        prob = mp_smooth/mp_smooth.sum()
        
        
        assert(len(angles) == len(mp))
        assert(len(mp) == len(mp_smooth))
                     
        L = 100
        a = subsample_fixed_length(angles, L)
        x = subsample_fixed_length(prob, L)
        
        map_prob.update_probability(ith, angles, x)
        prob_updated[ith] = True
        
    else:
        print('{0} not received'.format(ith))
        
    print('')
    plt.pause(0.01)
    

#for ith in antennas:
    # servos_sdrs.start(ith, speed=np.pi/5., run_on_stop_read=lambda: plot_step(ith))
servos_sdrs.start(0, speed=np.pi/5., run_on_stop_read=lambda: plot_step(0))
#servos_sdrs.start(1, speed=np.pi/5., run_on_stop_read=lambda: plot_step(1))

try:
    while True:
        for ith in antennas:
            if prob_updated[ith]:
                map_prob.draw_map(ith)
        plt.pause(0.5)
except KeyboardInterrupt:
    print('Exited')

for ith in antennas:
    servos_sdrs.stop(ith)


