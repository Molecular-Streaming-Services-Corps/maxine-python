def process_joystick_data(joystick_data):
    binary_string = bin(joystick_data)[2:]
    return process_joystick_string(binary_string)

def process_joystick_string(binary_string):
    button_names = ['up', 'down', 'left', 'right', 'b1', 'b2']
    all_buttons = ['js1_' + b for b in button_names] + ['not_used'] * 2 + ['js2_' + b for b in button_names] + ['not_used'] * 2
    
    pressed = []

    for i, bit in enumerate(reversed(binary_string)):
        if bit == '0':
            button = all_buttons[i]
            if button != 'not_used':
                pressed.append(button)
                
    return pressed

