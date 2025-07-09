import psutil

def check_state(pid: int):
    return psutil.Process(pid).is_running()

def kill_process(pid):
    print(f'Exited pid: {pid}')
    psutil.Process(pid).kill()