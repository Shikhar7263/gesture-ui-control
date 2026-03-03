import logging
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class PerformanceMonitor:
    def __init__(self):
        self.start_time = None

    def start(self):
        self.start_time = time.time()
        logging.debug('Performance monitoring started.')

    def stop(self):
        if self.start_time is None:
            logging.error('Performance monitoring was not started.')
            return None
        elapsed_time = time.time() - self.start_time
        logging.debug(f'Performance monitoring stopped. Elapsed time: {elapsed_time:.2f} seconds')
        return elapsed_time

# Example usage
# monitor = PerformanceMonitor()
# monitor.start()
# ... some code to monitor ...
# elapsed = monitor.stop()