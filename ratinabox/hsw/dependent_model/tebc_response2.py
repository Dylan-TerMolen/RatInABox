import numpy as np

# Define the timing of stimuli in seconds
CS_duration = 0.25  # 250 ms
US_start_time = CS_duration + 0.5  # 500 ms after the end of CS
US_duration = 0.100


# Cell type 1: bimodal with peaks as a multiple of the baseline
def gaussian_peak(time_since_CS, magnitude, peak_time, sd, baseline):
    # Gaussian response calculation
    response = magnitude * np.exp(-((time_since_CS - peak_time) ** 2) / (2 * sd ** 2))
    # Apply Gaussian response only near the peak time
    response = np.where(time_since_CS, response + baseline, baseline)
    return response
def bimodal_response(time_since_CS, magnitudes, peak_times, sds, baseline, cs_duration, us_duration):
    peak1 = gaussian_peak(time_since_CS, magnitudes[0], peak_times[0], sds[0], baseline)
    peak2 = gaussian_peak(time_since_CS, magnitudes[1], peak_times[1], sds[1], baseline)
    return peak1 + peak2


# Cell type 2: Gaussian peak with a multiple of the baseline
def gaussian_peak2(time_since_CS, magnitude, peak_time, sd, duration, baseline):
    response = magnitude * np.exp(-((time_since_CS - peak_time) ** 2) / (2 * sd ** 2)) + baseline
    if time_since_CS>peak_time-1/10:
        return response
    else:
        return baseline

# Cell type 3: Linear decay response, changes relative to baseline
def linear_decay_response(time_since_CS, baseline, peak_time, mid_time, end_time, first_magnitude, second_magnitude):
    if time_since_CS <= 0:
        return baseline
    elif 0 < time_since_CS < .2:
        slope = (first_magnitude - baseline) / .2
        return slope * (time_since_CS) + baseline
    elif .2 <= time_since_CS < .85:
        slope = (second_magnitude - first_magnitude) / .65
        return slope * (time_since_CS - mid_time) + first_magnitude + first_magnitude
    elif time_since_CS <= end_time+3:
        return second_magnitude
    else:
        return baseline

# Cell type 4: Adjusting the peaks to be a function of baseline
#type 4
def cell_type_4_response(time_since_CS, baseline, cs_peak, us_peak, cs_sd, us_sd, cs_decay_start, us_peak_time, us_duration):
    # Parameters for the response function
    if time_since_CS <= .05:
        total_response = baseline
    if .05<time_since_CS<=.78:
        slope = (cs_peak-baseline)/.73
        total_response =  slope * (time_since_CS-.05) + baseline
    if .78<time_since_CS<=1:
        total_response = us_peak * np.exp(-((time_since_CS - .78) ** 2) / (5 * us_sd ** 5)) + baseline
    # After the US duration, return to baseline
    if 1<time_since_CS<=3:
        total_response = cs_peak
    if time_since_CS>=3:
        total_response = baseline
    if total_response<cs_peak:
        total_response = cs_peak
    if total_response>us_peak:
        total_response = us_peak
    return total_response


# Cell type 5: Sharp increase to a peak that's a multiple of the baseline
def cell_type_5_function(time_since_CS, baseline, us_peak, us_duration):
    us_peak_time = US_start_time  # Assuming peak is right at the start of US
    # Start with a baseline
    response = baseline
    # Sharp increase to US peak
    if US_start_time <= time_since_CS < (US_start_time + us_duration):
        response = np.interp(time_since_CS, [.75, .78], [baseline, us_peak])
    # Linear decay from US peak back to baseline
    if us_peak_time <= time_since_CS:
        response = np.interp(time_since_CS, [.78, 1.2], [us_peak, baseline])
    return response

# Cell type 6: Noisy response around the baseline
def noisy_uniform_response(time_since_CS, baseline, noise_level=0.03/30):
    CS_duration = 0.25  # 250 ms
    US_start_time = CS_duration + 0.5  # 500 ms after the end of CS
    US_duration = 0.100
    return baseline + np.random.normal(-noise_level, noise_level)

# Cell type 7: Bimodal with peaks as a multiple of the baseline
def gaussian_peak3(time_since_CS, magnitude, peak_time, sd, duration, baseline):
    response = magnitude * np.exp(-((time_since_CS - peak_time) ** 2) / (2 * sd ** 2))
    # Apply Gaussian response only near the peak time and ensure it doesn't exceed the magnitude
    response = np.where((time_since_CS >= peak_time - 3*sd) & (time_since_CS <= peak_time + duration), response, 0)
    # Ensure response does not fall below baseline
    response += baseline
    return response
def bimodal_response2(time_since_CS, magnitudes, peak_times, sds, baseline, cs_duration, us_duration):
    peak1 = gaussian_peak3(time_since_CS, magnitudes[0], peak_times[0], sds[0], cs_duration, baseline)
    peak2 = gaussian_peak3(time_since_CS, magnitudes[1], peak_times[1], sds[1], us_duration, baseline)
    total_response = peak1 + peak2
    # Ensure the total response does not go below baseline at any point
    total_response = np.maximum(total_response, baseline)
    return total_response

# Cell type 8: Decay response with change as a proportion of baseline
def type8decay(time_since_CS, baseline):
    if time_since_CS <= .25:
        return baseline
    elif .25 < time_since_CS <= .252:
        return baseline*.46
    elif .252 <= time_since_CS < .75:
        slope = ((.62*baseline) - baseline) / (.75-.252)
        return slope * (time_since_CS - .252) + baseline
    elif .75<=time_since_CS <= 1.5:
        slope = ((.38*baseline) - baseline) / .75
        return slope * (time_since_CS - .75) + baseline
    else:
        return baseline



response_profiles = {
    1: {'response_func': lambda t, baseline: bimodal_response(t, [baseline * 2.14, baseline * 5.71], [0.3, .85], [0.1, 0.1], baseline, CS_duration, US_duration),},
    2: {'response_func': lambda t, baseline: gaussian_peak2(t, baseline * 3.14, US_start_time, 0.15, US_duration, baseline),},
    3: {'response_func': lambda t, baseline: linear_decay_response(t, baseline=baseline, peak_time=0, mid_time=.2, end_time=.85, first_magnitude=baseline*.33, second_magnitude=baseline*.17),},
    4: {'response_func': lambda t, baseline: cell_type_4_response(t, baseline, baseline * .4, baseline * 1.1, cs_sd=0.1, us_sd=0.2, cs_decay_start=.25, us_peak_time=.75, us_duration=0.1 ),},
    5: {'response_func': lambda t, baseline: cell_type_5_function(t, baseline, baseline * 3.14, US_duration),},
    6: {'response_func': lambda t, baseline: noisy_uniform_response(t, baseline),},
    7: {'response_func': lambda t, baseline: bimodal_response2(t, [baseline * 1.67, baseline * 2.14], [0.3, US_start_time + .05], [0.08, 0.15], baseline, cs_duration=.25, us_duration=.1),},
    8: {'response_func': lambda t, baseline: type8decay(t, baseline),}
}
