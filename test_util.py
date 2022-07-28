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

if __name__ == '__main__':
    test_process_joystick_string()

