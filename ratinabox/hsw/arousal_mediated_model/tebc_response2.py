import numpy as np

# Constants for timings

CS_duration = 0.25  # CS duration in seconds
CS_to_US_delay = 0.5  # Delay between CS and US in seconds
US_time = CS_duration + CS_to_US_delay  # Time when US occurs
US_pulse_duration = 0.1  # matches the 100ms US stimulus itself


def type_one_response(time_since_CS, baseline): #in place field firing, running
    """
    This cell type is elevated through the CS and trace interval (the
    hippocampal "bridging" signature expected of a trace-conditioned cell),
    then peaks again more strongly during the US itself before returning to
    baseline.
    """
    cs_trace_increase_factor = 1.3
    us_increase_factor = 1.5

    if time_since_CS < US_time:
        return baseline * cs_trace_increase_factor  # elevated through CS + trace
    elif time_since_CS < US_time + US_pulse_duration:
        return baseline * us_increase_factor  # strongest response during the US
    else:
        return baseline


def type_two_response(time_since_CS, baseline): #out of place field, running
    """
    This cell type shows a slight, sustained increase through the CS, trace
    interval, and US.
    """
    if time_since_CS < US_time + US_pulse_duration:
        return baseline * 1.1
    else:
        return baseline  # Remain at slight increase after US


def type_three_response(time_since_CS, baseline): #not moving, in field
    if time_since_CS < CS_duration:
        # Sudden increase at the start of CS
        return baseline * 1.5
    elif CS_duration <= time_since_CS < US_time:
        # Gradual decrease after the sudden increase, assuming a linear decrease for simplicity
        decrease_factor = 1 - (time_since_CS - CS_duration) / (US_time - CS_duration)
        return baseline * (1 + (0.5 * decrease_factor))
    elif time_since_CS < US_time + US_pulse_duration:
        # Large spike at US and then return to baseline
        return baseline * 3
    else:
        return baseline


def type_four_response(time_since_CS, baseline): #not moving, out of field
    CS_duration = 0.25  # CS duration in seconds
    CS_to_US_delay = 0.5  # Delay between CS and US in seconds
    US_time = CS_duration + CS_to_US_delay  # Time when US occurs
    total_time = CS_duration + CS_to_US_delay + 0.25  # Total duration considered for response
    # Random fluctuation throughout the period
    fluctuation = np.random.uniform(-0.2, 0.2) * baseline
    return baseline + fluctuation
