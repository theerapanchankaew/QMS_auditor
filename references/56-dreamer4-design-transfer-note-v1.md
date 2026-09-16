# Dreamer 4 Design Transfer Note for AIAS vNext

## Source role
This is a non-normative research transfer note based on the user-provided paper *Training Agents Inside of Scalable World Models* (Hafner, Yan, Lillicrap; Dreamer 4). It is an architecture inspiration only and must never be cited as an ISO requirement or certification criterion.

## Transferable ideas
- Learn a model of environment dynamics and use it to evaluate candidate action trajectories before real interaction.
- Separate world-model pretraining, task/policy adaptation, and imagination-based policy improvement.
- Use offline experience when live interaction is costly, unsafe, or inappropriate.
- Keep action conditioning explicit so predicted next states depend on both current state and selected action.

## AIAS adaptation
AIAS replaces pixels/game mechanics with structured Requirement, Evidence, and Process worlds. It replaces game reward with bounded audit utility such as evidence gain and uncertainty resolution. It retains a deterministic Process Enforcer outside the predictive model so simulation cannot become a finding.

## Non-transferable implementation detail
Do not copy Dreamer 4's video-generation architecture, GPU/TPU scale, diffusion/shortcut-forcing objective, or raw-pixel tokenizer unless a separate R&D project demonstrates a direct audit use case. The AIAS target is a structured symbolic/semantic audit world model, not a video world model.
