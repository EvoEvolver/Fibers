
# Resonate Peak Search

- Get the resonate curve from experiment. Scan from 9100 to 9800. Store the result as variable `frequency` and `amplitude`.

- Count the number of minimums in the amplitude, store it in the variable `n_min`

- If the number of minimums is larger than 1, use low pass filter to remove the high frequency noise. Start from cutoff_frequency 0.7. Then, count the number of minimums again. If the minimum is more than 1, decrease the cutoff_frequency. Repeat this procedure until the number of minimums is 1. 

