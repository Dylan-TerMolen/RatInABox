STALE: this file describes an early design that used a balance parameter to blend
place and tEBC responses per neuron. The current implementation (TEBC.py,
tebc_response2.py) is exclusively additive -- every task-responsive neuron's firing is
place_response + task_response, with no balance/blend parameter anywhere (no
balance_distribution, no percent_task_in_response_* -- those apply only to the
independent/place_dependent models, and args_parser.py's MODEL_REQUIRED_PARAMS for
'arousal_mediated' is empty, so the CLI rejects them for this model). The response
actually selected is a function of the animal's (in_field, running) state, not a
per-neuron balance draw. Left below for historical context on the model's original
motivation (transferring tEBC responses across environments while place responses
remap) -- the "balance_distribution" mentions are no longer accurate.

influence_learning:
- place response changes from envA to envB
- tebc response is mantained
- can still adjust ratio of place to tebc

in EnvA, neurons develop a combined response of place cells and tEBC, while in EnvB, the place cell response is recalibrated for the new environment, but the tEBC response remains as established in EnvA. This setup is ideal for studying the transfer of task-specific information (tEBC) across different spatial contexts (EnvA and EnvB) while maintaining the unique spatial encoding of each environment through place cells.

ok, this model is built to focus on understanding the limits of task-specific information transfer (tebc transfer) without compromising the specificity and accuracy of place cells. To do this i am modeling cell responses to tebc and place and combining them using  a BALANCE PARAMETER to adjust how much each cell incorporates spatial vs tEBC data, and a  tebc_responsive_rate parameter that specifies the percentage of neurons that are responsive to tEBC signals. An agent is then modeled in envA, where it establishes cells with a combined tebc and place response. the agent is then run in environment B. since this is a new environment, the place cell contirbution to cell responses should be completely new. however, since the tebc task is the same, the contribution to cell responses from tebc should remain the same as in env A.

1.
tEBC Responses Maintained from EnvA: By setting combined_neurons.tebc_responsive_neurons to
tebc_responsive_neurons_envA in EnvB, you preserve the tEBC response characteristics that were
determined in EnvA. This means the tEBC component of your neuron model remains unchanged as the
agent transitions from EnvA to EnvB.
2.
New Place Responses for EnvB: By reinitializing the CombinedPlaceTebcNeurons instance for EnvB
with new place cell parameters (which should be reflective of EnvB's specific characteristics),
you generate place responses appropriate for EnvB.
3.
Combining Responses Based on balance_distribution and responsive_distribution: The way these
two responses (place and tEBC) are combined in each neuron is governed by the balance_distribution
and responsive_distribution parameters. These parameters should control the relative influence of
each response type on the overall firing rate of each neuron.
4.
Final Neuron Behavior in EnvB: As a result, in EnvB, each neuron's firing behavior will be a
combination of the unchanged tEBC response from EnvA and the new place response specific to EnvB,
merged according to the rules defined by your balance and responsive distributions.

This approach allows for a nuanced model where learning from one environment (in terms of tEBC responses)
can be transferred and combined with new spatial information (place responses) from another environment,
reflecting a form of contextual learning and adaptation.
