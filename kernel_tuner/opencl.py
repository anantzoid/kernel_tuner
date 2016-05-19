"""This module contains all OpenCL specific kernel_tuner functions"""
import numpy

#embedded in try block to be able to generate documentation
try:
    import pyopencl as cl
except Exception:
    pass


class OpenCLFunctions(object):
    """Class that groups the OpenCL functions on maintains some state about the device"""

    def __init__(self, device=0, iterations=7):
        """Creates OpenCL device context and reads device properties

        :param device: The ID of the OpenCL device to use for benchmarking
        :type device: int

        :param iterations: The number of iterations to run the kernel during benchmarking, 7 by default.
        :type iterations: int
        """
        self.ITERATIONS = iterations
        #setup context and queue
        platforms = cl.get_platforms()
        self.ctx = cl.Context(dev_type=cl.device_type.ALL,
                properties=[(cl.context_properties.PLATFORM, platforms[device])])
        self.queue = cl.CommandQueue(self.ctx, properties=cl.command_queue_properties.PROFILING_ENABLE)
        self.mf = cl.mem_flags
        #inspect device properties
        self.max_threads = self.ctx.devices[0].get_info(cl.device_info.MAX_WORK_GROUP_SIZE)

    def create_gpu_args(self, arguments):
        """ready argument list to be passed to the kernel, allocates gpu mem

        :param arguments: List of arguments to be passed to the kernel.
            The order should match the argument list on the OpenCL kernel.
            Allowed values are numpy.ndarray, and/or numpy.int32, numpy.float32, and so on.
        :type arguments: list(numpy objects)

        :returns: A list of arguments that can be passed to an OpenCL kernel.
        :rtype: list( pyopencl.Buffer, numpy.int32, ... )
        """
        gpu_args = []
        for arg in arguments:
            # if arg i is a numpy array copy to device
            if isinstance(arg, numpy.ndarray):
                gpu_args.append(cl.Buffer(self.ctx, self.mf.READ_WRITE | self.mf.COPY_HOST_PTR, hostbuf=arg))
            else: # if not an array, just pass argument along
                gpu_args.append(arg)
        return gpu_args

    def compile(self, kernel_name, kernel_string):
        """call the OpenCL compiler to compile the kernel, return the device function

        :param kernel_name: The name of the kernel to be compiled, used to lookup the
            function after compilation.
        :type kernel_name: string

        :param kernel_string: The OpenCL kernel code that contains the function `kernel_name`
        :type kernel_string: string

        :returns: An OpenCL kernel that can be called directly.
        :rtype: pyopencl.Kernel
        """
        prg = cl.Program(self.ctx, kernel_string).build()
        func = getattr(prg, kernel_name)
        return func

    def benchmark(self, func, gpu_args, threads, grid):
        """runs the kernel and measures time repeatedly, returns average time

        Runs the kernel and measures kernel execution time repeatedly, number of
        iterations is set during the creation of OpenCLFunctions. Benchmark returns
        a robust average, from all measurements the fastest and slowest runs are
        discarded and the rest is included in the returned average. The reason for
        this is to be robust against initialization artifacts and other exceptional
        cases.

        :param func: A PyOpenCL kernel compiled for this specific kernel configuration
        :type func: pyopencl.Kernel

        :param gpu_args: A list of arguments to the kernel, order should match the
            order in the code. Allowed values are either variables in global memory
            or single values passed by value.
        :type gpu_args: list( pyopencl.Buffer, numpy.int32, ...)

        :param threads: A tuple listing the number of work items in each dimension of
            the work group.
        :type threads: tuple(int, int, int)

        :param grid: A tuple listing the number of work groups in each dimension
            of the NDRange.
        :type grid: tuple(int, int)

        :returns: A robust average for the kernel execution time.
        :rtype: float
        """
        global_size = (grid[0]*threads[0], grid[1]*threads[1], threads[2])
        local_size = threads
        times = []
        for _ in range(self.ITERATIONS):
            event = func(self.queue, global_size, local_size, *gpu_args)
            event.wait()
            times.append((event.profile.end - event.profile.start)*1e-6)
        times = sorted(times)
        return numpy.mean(times[1:-1])

    def run_kernel(self, func, gpu_args, threads, grid):
        """runs the OpenCL kernel passed as 'func'

        :param func: An OpenCL Kernel
        :type func: pyopencl.Kernel

        :param gpu_args: A list of arguments to the kernel, order should match the
            order in the code. Allowed values are either variables in global memory
            or single values passed by value.
        :type gpu_args: list( pyopencl.Buffer, numpy.int32, ...)

        :param threads: A tuple listing the number of work items in each dimension of
            the work group.
        :type threads: tuple(int, int, int)

        :param grid: A tuple listing the number of work groups in each dimension
            of the NDRange.
        :type grid: tuple(int, int)
        """
        global_size = (grid[0]*threads[0], grid[1]*threads[1], threads[2])
        local_size = threads
        event = func(self.queue, global_size, local_size, *gpu_args)
        event.wait()

    def memset(self, buffer, value, size):
        """set the memory in allocation to the value in value

        :param allocation: An OpenCL Buffer to fill
        :type allocation: pyopencl.Buffer

        :param value: The value to set the memory to
        :type value: a single 32-bit float or int

        :param size: The size of to the allocation unit
        :type size: int

        """
        if isinstance(buffer, cl.Buffer):
            cl.enqueue_fill_buffer(self.queue, buffer, numpy.array(value), 0, size)

    def memcpy_dtoh(self, dest, src):
        """perform a device to host memory copy

        :param dest: A numpy array in host memory to store the data
        :type dest: numpy.ndarray

        :param src: An OpenCL Buffer to copy data from
        :type src: pyopencl.Buffer
        """
        if isinstance(src, cl.Buffer):
            cl.enqueue_copy(self.queue, dest, src)



