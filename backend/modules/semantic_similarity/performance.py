import os
import time
import json
import hashlib
import asyncio
import functools
from typing import List, Dict, Tuple, Optional, Callable, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)

# -------------------------
# Caching Decorator
# -------------------------

class LRUCache:
    """Simple LRU cache with TTL support"""

    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 3600):
        self.maxsize = maxsize
        self.ttl = ttl_seconds
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.access_order: List[str] = []

    def _hash_key(self, *args, **kwargs) -> str:
        """Generate hash key from arguments"""
        key_data = json.dumps((args, sorted(kwargs.items())), default=str)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if valid"""
        if key not in self.cache:
            return None

        value, timestamp = self.cache[key]

        # Check TTL
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            return None

        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

        return value

    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        # Evict oldest if at capacity
        while len(self.cache) >= self.maxsize and self.access_order:
            oldest_key = self.access_order.pop(0)
            self.cache.pop(oldest_key, None)

        self.cache[key] = (value, time.time())
        self.access_order.append(key)

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.access_order.clear()

    @property
    def size(self) -> int:
        return len(self.cache)


def cached(cache: LRUCache = None, ttl: int = 3600):
    """
    Decorator for caching function results

    Usage:
        @cached(ttl=3600)
        def expensive_function(x, y):
            ...
    """
    if cache is None:
        cache = LRUCache(ttl_seconds=ttl)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = cache._hash_key(func.__name__, *args, **kwargs)
            result = cache.get(key)

            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result

            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        wrapper.cache = cache
        wrapper.clear_cache = cache.clear
        return wrapper

    return decorator


# Global caches for different purposes
similarity_cache = LRUCache(maxsize=5000, ttl_seconds=3600)
embedding_cache = LRUCache(maxsize=2000, ttl_seconds=7200)




@dataclass
class BatchResult:
    """Result from batch processing"""
    index: int
    result: Any
    error: Optional[str] = None
    processing_time: float = 0.0


class BatchProcessor:
    """
    Process multiple items in parallel for improved throughput
    """

    def __init__(self, max_workers: int = 4, timeout: float = 30.0):
        self.max_workers = max_workers
        self.timeout = timeout

    def process(
        self,
        items: List[Any],
        process_func: Callable,
        *args,
        **kwargs
    ) -> List[BatchResult]:
        """
        Process items in parallel

        Args:
            items: List of items to process
            process_func: Function to apply to each item
            *args, **kwargs: Additional arguments for process_func

        Returns:
            List of BatchResult objects
        """
        results: List[BatchResult] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}

            for idx, item in enumerate(items):
                future = executor.submit(
                    self._process_single,
                    idx, item, process_func, args, kwargs
                )
                futures[future] = idx

            for future in as_completed(futures, timeout=self.timeout):
                idx = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(BatchResult(
                        index=idx,
                        result=None,
                        error=str(e)
                    ))

        
        results.sort(key=lambda x: x.index)
        return results

    def _process_single(
        self,
        index: int,
        item: Any,
        func: Callable,
        args: tuple,
        kwargs: dict
    ) -> BatchResult:
        """Process a single item with timing"""
        start_time = time.time()
        try:
            result = func(item, *args, **kwargs)
            return BatchResult(
                index=index,
                result=result,
                processing_time=time.time() - start_time
            )
        except Exception as e:
            return BatchResult(
                index=index,
                result=None,
                error=str(e),
                processing_time=time.time() - start_time
            )


def batch_process_texts(
    text_pairs: List[Tuple[str, str]],
    detector_func: Callable,
    max_workers: int = 4
) -> List[Dict]:
    """
    Process multiple text pairs for plagiarism detection

    Args:
        text_pairs: List of (original, suspicious) text pairs
        detector_func: Function that takes (text1, text2) and returns result
        max_workers: Number of parallel workers

    Returns:
        List of detection results
    """
    processor = BatchProcessor(max_workers=max_workers)

    def process_pair(pair: Tuple[str, str]) -> Dict:
        text1, text2 = pair
        return detector_func(text1, text2)

    batch_results = processor.process(text_pairs, process_pair)

    return [
        {
            "index": r.index,
            "result": r.result,
            "error": r.error,
            "processing_time": r.processing_time
        }
        for r in batch_results
    ]




async def async_batch_process(
    items: List[Any],
    async_func: Callable,
    max_concurrent: int = 5
) -> List[Any]:
    """
    Process items asynchronously with concurrency limit

    Args:
        items: List of items to process
        async_func: Async function to apply
        max_concurrent: Maximum concurrent operations

    Returns:
        List of results in order
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_process(item, index):
        async with semaphore:
            try:
                result = await async_func(item)
                return (index, result, None)
            except Exception as e:
                return (index, None, str(e))

    tasks = [
        bounded_process(item, idx)
        for idx, item in enumerate(items)
    ]

    results = await asyncio.gather(*tasks)

   
    sorted_results = sorted(results, key=lambda x: x[0])
    return [r[1] for r in sorted_results]




class PerformanceMonitor:
    """Track and report performance metrics"""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}

    def record(self, operation: str, duration: float) -> None:
        """Record a duration for an operation"""
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)

    def get_stats(self, operation: str = None) -> Dict:
        """Get statistics for operations"""
        if operation:
            if operation not in self.metrics:
                return {}
            times = self.metrics[operation]
            return self._calculate_stats(operation, times)

        return {
            op: self._calculate_stats(op, times)
            for op, times in self.metrics.items()
        }

    def _calculate_stats(self, operation: str, times: List[float]) -> Dict:
        if not times:
            return {}
        return {
            "operation": operation,
            "count": len(times),
            "total": sum(times),
            "mean": sum(times) / len(times),
            "min": min(times),
            "max": max(times)
        }

    def clear(self) -> None:
        """Clear all metrics"""
        self.metrics.clear()



perf_monitor = PerformanceMonitor()


def timed(operation_name: str = None):
    """
    Decorator to time function execution and record metrics

    Usage:
        @timed("similarity_calculation")
        def calculate_similarity(text1, text2):
            ...
    """
    def decorator(func: Callable) -> Callable:
        name = operation_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                perf_monitor.record(name, duration)

        return wrapper
    return decorator




def chunked_process(
    items: List[Any],
    process_func: Callable,
    chunk_size: int = 100
) -> List[Any]:
    """
    Process items in chunks to manage memory

    Args:
        items: List of items
        process_func: Function to process a chunk
        chunk_size: Size of each chunk

    Returns:
        Combined results
    """
    results = []

    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]
        chunk_results = process_func(chunk)
        results.extend(chunk_results)

        
        logger.debug(f"Processed chunk {i // chunk_size + 1}")

    return results




def get_cache_stats() -> Dict:
    """Get statistics for all caches"""
    return {
        "similarity_cache": {
            "size": similarity_cache.size,
            "maxsize": similarity_cache.maxsize,
            "ttl_seconds": similarity_cache.ttl
        },
        "embedding_cache": {
            "size": embedding_cache.size,
            "maxsize": embedding_cache.maxsize,
            "ttl_seconds": embedding_cache.ttl
        }
    }


def clear_all_caches() -> None:
    """Clear all caches"""
    similarity_cache.clear()
    embedding_cache.clear()
    logger.info("All caches cleared")


def get_performance_stats() -> Dict:
    """Get all performance statistics"""
    return {
        "cache_stats": get_cache_stats(),
        "timing_stats": perf_monitor.get_stats()
    }


if __name__ == "__main__":
    
    print("=" * 60)
    print("PERFORMANCE UTILITIES TEST")
    print("=" * 60)

    
    @cached(ttl=60)
    def slow_function(x):
        time.sleep(0.1)
        return x * 2

    print("\nTesting cache...")
    start = time.time()
    result1 = slow_function(5)
    time1 = time.time() - start

    start = time.time()
    result2 = slow_function(5)  
    time2 = time.time() - start

    print(f"First call: {time1:.4f}s, result: {result1}")
    print(f"Cached call: {time2:.4f}s, result: {result2}")
    print(f"Cache speedup: {time1/time2:.1f}x")

    # Test batch processing
    print("\nTesting batch processing...")
    processor = BatchProcessor(max_workers=4)

    def square(x):
        time.sleep(0.1)
        return x ** 2

    items = list(range(10))
    start = time.time()
    results = processor.process(items, square)
    batch_time = time.time() - start

    print(f"Processed {len(items)} items in {batch_time:.2f}s")
    print(f"Results: {[r.result for r in results]}")

    
    print("\nTesting performance monitoring...")

    @timed("test_operation")
    def test_op():
        time.sleep(0.05)

    for _ in range(5):
        test_op()

    stats = perf_monitor.get_stats("test_operation")
    print(f"Performance stats: {stats}")

    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)
