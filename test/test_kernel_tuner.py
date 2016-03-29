import numpy
import pycuda.driver

from .context import kernel_tuner

def test_create_gpu_args():

    size = 1000
    a = 0.75
    b = numpy.random.randn(size).astype(numpy.float32)
    c = numpy.zeros_like(b)

    arguments = [c, a, b]

    gpu_args = kernel_tuner._create_gpu_args(arguments)

    assert type(gpu_args[0]) is pycuda.driver.DeviceAllocation
    assert type(gpu_args[1]) is float
    assert type(gpu_args[2]) is pycuda.driver.DeviceAllocation

    gpu_args[0].free()
    gpu_args[2].free()


def test_get_grid_dimensions():

    problem_size = (1024, 1024)

    params = dict()
    params["block_x"] = 41
    params["block_y"] = 37

    grid_div_x = ["block_x"]
    grid_div_y = ["block_y"]

    grid = kernel_tuner._get_grid_dimensions(problem_size, params,
                    grid_div_y, grid_div_x)

    assert len(grid) == 2
    assert type(grid[0]) is int
    assert type(grid[1]) is int

    print grid
    assert grid[0] == 25
    assert grid[1] == 28

    grid = kernel_tuner._get_grid_dimensions(problem_size, params,
                    None, grid_div_x)

    print grid
    assert grid[0] == 25
    assert grid[1] == 1024

    grid = kernel_tuner._get_grid_dimensions(problem_size, params,
                    grid_div_y, None)

    print grid
    assert grid[0] == 1024
    assert grid[1] == 28

    return grid


def test_get_thread_block_dimensions():

    params = dict()
    params["block_size_x"] = 123
    params["block_size_y"] = 257

    threads = kernel_tuner._get_thread_block_dimensions(params)
    assert len(threads) == 3
    assert type(threads[0]) is int
    assert type(threads[1]) is int
    assert type(threads[2]) is int

    assert threads[0] == 123
    assert threads[1] == 257
    assert threads[2] == 1