# Commented-out code preserved here for reference.
# These blocks were removed from the main2.py files to reduce clutter.


# ── PLOTTING ──────────────────────────────────────────────────────────────────
# Used in: additive_model/main2.py, dependent_model/main2.py, place_dep_model/main2.py

# ratinabox.autosave_plots = True
# ratinabox.stylize_plots()
# plt.show()
# agentA.plot_trajectory()
# plt.show()
# agentA.plot_position_heatmap()
# plt.show()
# agentA.plot_histogram_of_speeds()
# plt.show()
# agentB.plot_histogram_of_speeds()
# plt.show()
# combined_neuronsA.plot_rate_timeseries()
# plt.show()
# combined_neuronsA.plot_rate_map()
# plt.show()
# combined_neuronsA.plot_place_cell_locations()
# plt.show()


# ── SAVE: additive_model firing rates to .npy ─────────────────────────────────
# Used in: additive_model/main2.py

# filename_envA = f"AM_response_envA_balance_{balance_value}_{args.balance_dist}_responsive_{responsive_val}_{args.responsive_type}_perPCs_{percent_place_cell}.npy"
# filename_envB = f"AM_response_envB_balance_{balance_value}_{args.balance_dist}_responsive_{responsive_val}_{args.responsive_type}_perPCs_{percent_place_cell}.npy"
# full_path_envA = os.path.join(save_directory, filename_envA)
# full_path_envB = os.path.join(save_directory, filename_envB)
# np.save(full_path_envA, spikesA)
# np.save(full_path_envB, spikesB)
# np.save(full_path_envA, firingrate_envA)
# np.save(full_path_envB, firingrate_envB)


# ── SAVE: dependent_model firing rates to .npy ────────────────────────────────
# Used in: dependent_model/main2.py

# filename_envA = f"DM_response_envA_balance_{balance_value}_{args.balance_dist}_responsive_{responsive_val}_{args.responsive_type}_perPCs_{percent_place_cell}.npy"
# filename_envB = f"DM_response_envB_balance_{balance_value}_{args.balance_dist}_responsive_{responsive_val}_{args.responsive_type}_perPCs_{percent_place_cell}.npy"
# full_path_envA = os.path.join(save_directory, filename_envA)
# full_path_envB = os.path.join(save_directory, filename_envB)
# np.save(full_path_envA, spikesA)
# np.save(full_path_envB, spikesB)
# np.save(full_path_envA, firingrate_envA)
# np.save(full_path_envB, firingrate_envB)


# ── SAVE: raw position and spikes to hardcoded paths (additive_model) ─────────
# Used in: additive_model/main2.py

# filename_envA = f"ratinabox_pos"
# if work:
#     full_path_envA = os.path.join('/home/hsw967/Programming/data_eyeblink/rat314/trainingdata', filename_envA)
# else:
#     full_path_envA = os.path.join('/Users/Hannah/Programming/data_eyeblink/rat314/trainingdata', filename_envA)
# np.save(full_path_envA, posA)
#
# filename_envA = f"ratinabox_spikes"
# if work:
#     full_path_envA = os.path.join('/home/hsw967/Programming/data_eyeblink/rat314/trainingdata', filename_envA)
# else:
#     full_path_envA = os.path.join('/Users/Hannah/Programming/data_eyeblink/rat314/trainingdata', filename_envA)
# np.save(full_path_envA, response_envA)


# ── MISC: commented single-line calls ─────────────────────────────────────────

# pos_test_scoreB, pos_test_errB, dis_meanB, dis_medianB, pos_test_score_shuffB, pos_test_err_shuffB, dis_mean_shuffB, dis_median_shuffB = pos_decoding_self(response_envB, posB, .70)
