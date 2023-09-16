from ablator.mp.utils import ray_init
from ablator.utils.progress_bar import (
    num_format,
    ProgressBar,
    RemoteProgressBar,
    RemoteDisplay,
)
import numpy as np
from pathlib import Path
import time
from collections import defaultdict
import ray
from multiprocessing import Process


def _assert_num_format(num, width):
    str_num = num_format(num, width)
    float_num = float(str_num)
    relative_error = (num - float_num) / (num + 1e-5)
    assert len(str_num) == width
    assert relative_error < 1e-5
    print(str_num)


def test_num_format():
    nums = [
        100000000000000000000000000000,
        100000000,
        100,
        100.000,
        0,
        0.0000,
        0.001,
        0.00000001,
        0.00000000001,
        1.0000000000001,
        10000000001.0010000000,
        10000000001.002000000,
        10000000001.00000000000,
        10000000001.0000000000001,
        10000000001.0000000000,
        10000000001.00000000000010000000000,
    ]
    widths = [8, 10, 12, 15, 200]
    for width in widths[::-1]:
        for i, num in enumerate(nums):
            for sign in [-1, 1]:
                _num = sign * num
                _assert_num_format(_num, width)
                _assert_num_format(np.float32(_num), width)
                try:
                    _assert_num_format(np.longlong(_num), width)
                except OverflowError:
                    pass


def _measure_dur(num):
    start = time.time()
    num_format(num)
    end = time.time()
    return end - start


def _measure_dur_naive(num):
    start = time.time()
    s = f"{num:.5e}"
    end = time.time()
    return end - start


def test_perf():
    durs = defaultdict(list)
    for i in range(10000):
        i = np.random.randint(0, 10**8)
        durs["int"].append(_measure_dur(i))
        durs["int_naive"].append(_measure_dur_naive(i))
        i = np.random.rand() * i
        durs["float"].append(_measure_dur(i))
        durs["float_naive"].append(_measure_dur_naive(i))


def _rand_str(size=10):
    return "".join([chr(ord("a") + np.random.randint(26)) for i in range(size)])


def write_text(fp: Path, n=1000):
    with open(fp, "a") as f:
        for i in range(n):
            f.write(f"Some rand Log: {_rand_str(100)}\n")
            f.flush()
            time.sleep(0.5)
        pass


def _test_tui(tmp_path: Path, progress_bar=None):
    uid = _rand_str(10)
    fp = tmp_path.joinpath(uid)
    fp.write_text("")
    p = Process(target=write_text, args=(fp,))
    p.start()

    b = ProgressBar(100000, logfile=fp, remote_display=progress_bar, uid=uid)

    s = {_rand_str(): np.random.random() for i in range(100)}
    for i in b:
        for k, v in s.items():
            s[k] = np.random.random()
        b.update_metrics(s, i)
        time.sleep(0.1)
    return


def _test_tui_remote(tmp_path: Path):
    if not ray.is_initialized():
        ray_init()
    import random

    @ray.remote
    def test_remote(i, progress_bar: RemoteProgressBar):
        _test_tui(tmp_path, progress_bar)

    trials = 20
    progress_bar = RemoteProgressBar.remote(trials)

    dis = RemoteDisplay(progress_bar)

    remotes = []
    for i in range(trials):
        remotes.append(test_remote.remote(i, progress_bar))
        time.sleep(random.random())
        dis.refresh(force=True)
    while len(remotes) > 0:
        done_id, remotes = ray.wait(remotes, num_returns=1, timeout=0.1)
        dis.refresh()
        time.sleep(random.random() / 10)

from ablator.utils.progress_bar import in_notebook
def test_in_notebook():
    result=in_notebook()
    assert result==False,"The in_notebook function cannot correctly determine whether it is a terminal."
    with mock.patch('ablator.utils.progress_bar.in_notebook', side_effect=ImportError):
        result = in_notebook()
        assert result == False
    with mock.patch('ablator.utils.progress_bar.in_notebook',side_effect=AttributeError):
        result=in_notebook()
        assert result==False

from ablator.utils.progress_bar import get_last_line
def test_get_last_line():
    result=get_last_line(Path("hhhh.txt"))
    assert result==None
    result=get_last_line(None)
    assert result==None
    result=get_last_line(Path("/Users/vivi/Documents/USC/实习/Ablator/ablator_v0.0.1-mp/test2.txt"))
    assert result=="This is the last line."

def test_display_class():
    #test __init__ function of Display class
    display=Display()
    assert hasattr(display,"nrows") and hasattr(display,"ncols") and not hasattr(display,"html_value")

    #test _display function of Display class
    mock_display_instance = Display()
    mock_display_instance.ncols = None
    mock_display_instance._display("12345",0)
    last_line = mock_display_instance.stdscr.instr(0, 0, 5)
    assert last_line.decode('utf-8')=="     "
    display._display("12345",0)
    last_line=display.stdscr.instr(0,0,5)
    assert last_line.decode('utf-8')=="12345"
    display._refresh()

    #test _refresh function of Display class
    display._refresh()
    last_line = display.stdscr.instr(0, 0, 5)
    assert last_line.decode('utf-8')=="     "

    #test _update_screen_dims function of Display class
    nrows=display.nrows
    ncols=display.ncols
    display.stdscr.resize(nrows+1, ncols+1)
    display._update_screen_dims()
    nrows_update=display.nrows
    ncols_update=display.ncols
    assert nrows_update!=nrows and ncols_update!=ncols

    #test print_texts function of Display class
    #mainly to test the function of print_texts() could work well
    #this test has not completed!
    texts=["hello","world","!"]
    assert display.stdscr.instr(1,0,5)=="world"
    display.print_texts(texts)


if __name__ == "__main__":
    tmp_path = Path("/tmp/")
    # _test_tui(tmp_path)
    # _test_tui_remote(tmp_path)
