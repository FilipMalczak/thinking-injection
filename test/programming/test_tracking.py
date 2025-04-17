from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_programming.tracking import track, sample, periodically, tracker


@case
def sample_every_3_out_of_10():
    samples = []
    stream = range(10)
    for x in track(stream, sample(periodically(3), tracker(lambda x, y: samples.append((x, y))))):
        pass
    assert samples == [ (0, 0), (3, 3), (6, 6), (9, 9)]

if __name__ == "__main__":
    run_current_module()