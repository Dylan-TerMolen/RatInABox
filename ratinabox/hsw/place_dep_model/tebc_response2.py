import numpy as np

# Constants for timings

def type_one_response(time_since_CS, baseline): #in place field firing, running
    """
    This cell type shows a slight decrease during the CS period,
    a sharp decrease at the US, followed by an immediate increase after the US.
    """
    CS_duration = 0.25  # CS duration in seconds
    CS_to_US_delay = 0.5  # Delay between CS and US in seconds
    US_time = CS_duration + CS_to_US_delay  # Time when US occurs

    # A parameter to control how much the firing rate increases after US
    post_US_increase_factor = 1.2

    if time_since_CS < CS_duration:
        return baseline * 0.9  # Slight decrease during CS
    elif time_since_CS < US_time:
        return baseline  # Return to baseline after CS and before US
    elif time_since_CS == US_time:
        return baseline * 0.5  # Sharp decrease at US
    else:
        # Increase after US; the increase happens for a short period after US
        time_after_US = time_since_CS - US_time
        if time_after_US < 0.1:  # Assume the increase lasts for 100ms
            return baseline * post_US_increase_factor
        else:
            return baseline  # Return to baseline after the short increase


def type_two_response(time_since_CS, baseline): #out of place field, running
    """
    This cell type shows a slight increase during the CS and the US.
    """
    CS_duration = 0.25  # CS duration in seconds
    CS_to_US_delay = 0.5  # Delay between CS and US in seconds
    US_time = CS_duration + CS_to_US_delay  # Time when US occurs

    if time_since_CS < US_time:
        return baseline * 1.1  # No change during CS
    elif time_since_CS == US_time:
        return baseline * 1.1  # Slight increase at US
    else:
        return baseline  # Remain at slight increase after US

def type_three_response(time_since_CS, baseline): #not moving, in field
    CS_duration = 0.25  # CS duration in seconds
    CS_to_US_delay = 0.5  # Delay between CS and US in seconds
    US_time = CS_duration + CS_to_US_delay  # Time when US occurs
    total_time = CS_duration + CS_to_US_delay + 0.25  # Total duration considered for response
    if time_since_CS < CS_duration:
        # Sudden increase at the start of CS
        return baseline * 1.5
    elif CS_duration <= time_since_CS < US_time:
        # Gradual decrease after the sudden increase, assuming a linear decrease for simplicity
        decrease_factor = 1 - (time_since_CS - CS_duration) / (US_time - CS_duration)
        return baseline * (1 + (0.5 * decrease_factor))
    elif time_since_CS >= US_time:
        # Large spike at US and then return to baseline
        return baseline * 3 if time_since_CS == US_time else baseline


def type_four_response(time_since_CS, baseline): #not moving, out of field
    CS_duration = 0.25  # CS duration in seconds
    CS_to_US_delay = 0.5  # Delay between CS and US in seconds
    US_time = CS_duration + CS_to_US_delay  # Time when US occurs
    total_time = CS_duration + CS_to_US_delay + 0.25  # Total duration considered for response
    # Random fluctuation throughout the period
    fluctuation = np.random.uniform(-0.2, 0.2) * baseline
    return baseline + fluctuation
