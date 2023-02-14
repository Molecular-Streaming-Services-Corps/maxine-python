import numpy as np

import util

def test_process_joystick_string():
    # Simulate up and button 1 being pressed on joystick 1.
    # Got the bits backward.
    #controls = '011101' + '11' + '111111' + '11'
    controls = '11' + '111111' + '11' + '101110' 
    button_on_list = util.process_joystick_string(controls)
    print(button_on_list)
    correct_list = ['js1_up', 'js1_b1']
    print(button_on_list == correct_list)

def test_kurtosis():
    data = np.array([55.0, 78, 65, 98, 97, 60, 67, 65, 83, 65])
    
    K = util.kurtosis(data)
    
    print(K)
    print(K == 2.0453729382893173)

if __name__ == '__main__':
    test_process_joystick_string()
    test_kurtosis()

