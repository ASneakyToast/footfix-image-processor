#!/usr/bin/env python3
"""
Performance Testing and Profiling for FootFix
Measures performance metrics and identifies bottlenecks
"""

import sys
import os
import time
import cProfile
import pstats
import io
import tempfile
import shutil
import psutil
import gc
from pathlib import Path
from PIL import Image
import numpy as np
from memory_profiler import profile
import matplotlib.pyplot as plt

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from footfix.core.processor import ImageProcessor
from footfix.core.batch_processor import BatchProcessor


class PerformanceTester:
    """Performance testing and profiling for FootFix"""
    
    def __init__(self):
        self.results = {
            'single_image': {},
            'batch_processing': {},
            'memory_usage': {},
            'bottlenecks': []
        }
        self.temp_dir = None
    
    def setup(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"
        self.output_dir.mkdir()
        return self.temp_dir
    
    def cleanup(self):
        """Clean up test environment"""
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
    
    def create_test_images(self, count=50, size=(2000, 2000)):
        """Create test images for performance testing"""
        images = []
        for i in range(count):
            img = Image.new('RGB', size, 
                          color=(i*5 % 255, i*7 % 255, i*11 % 255))
            # Add some complexity to the image
            pixels = np.array(img)
            noise = np.random.randint(0, 50, size=(*size, 3))
            pixels = np.clip(pixels + noise, 0, 255).astype(np.uint8)
            img = Image.fromarray(pixels)
            
            img_path = Path(self.temp_dir) / f"perf_test_{i:04d}.jpg"
            img.save(img_path, quality=95)
            images.append(str(img_path))
        return images
    
    def profile_single_image(self):
        """Profile single image processing"""
        print("\n📊 Profiling Single Image Processing...")
        
        # Create test image
        test_img = self.create_test_images(1, size=(4000, 4000))[0]
        processor = ImageProcessor()
        
        # Profile the processing
        profiler = cProfile.Profile()
        profiler.enable()
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        result = processor.process_image(
            test_img,
            str(self.output_dir),
            resize_percent=50,
            quality=85,
            enable_sharpening=True,
            sharpen_amount=1.2
        )
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        profiler.disable()
        
        # Analyze results
        self.results['single_image'] = {
            'processing_time': end_time - start_time,
            'memory_used': end_memory - start_memory,
            'success': result['success']
        }
        
        # Get profiling stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions
        
        print(f"✅ Single image processing time: {self.results['single_image']['processing_time']:.2f}s")
        print(f"💾 Memory used: {self.results['single_image']['memory_used']:.2f}MB")
        
        # Identify bottlenecks
        ps.sort_stats('time')
        ps.print_stats(10)
        profile_output = s.getvalue()
        
        return profile_output
    
    def profile_batch_processing(self, batch_sizes=[10, 30, 50]):
        """Profile batch processing with different sizes"""
        print("\n📊 Profiling Batch Processing...")
        
        batch_processor = BatchProcessor()
        batch_results = {}
        
        for size in batch_sizes:
            print(f"\nTesting batch size: {size}")
            
            # Create test images
            test_images = self.create_test_images(size)
            
            # Clear memory
            gc.collect()
            
            # Measure performance
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            processed = 0
            def on_progress(current, total, message):
                nonlocal processed
                processed = current
            
            batch_processor.progress_updated.connect(on_progress)
            batch_processor.process_batch(
                test_images,
                str(self.output_dir),
                resize_percent=60,
                quality=85,
                enable_sharpening=True
            )
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            batch_results[size] = {
                'total_time': end_time - start_time,
                'time_per_image': (end_time - start_time) / size,
                'memory_used': end_memory - start_memory,
                'memory_per_image': (end_memory - start_memory) / size,
                'images_processed': processed
            }
            
            print(f"✅ Batch {size}: {batch_results[size]['total_time']:.2f}s total")
            print(f"⏱  Per image: {batch_results[size]['time_per_image']:.2f}s")
            print(f"💾 Memory: {batch_results[size]['memory_used']:.2f}MB total")
        
        self.results['batch_processing'] = batch_results
        return batch_results
    
    @profile
    def memory_profile_processing(self):
        """Detailed memory profiling of image processing"""
        print("\n📊 Memory Profiling...")
        
        # Create large test image
        test_img = self.create_test_images(1, size=(5000, 5000))[0]
        processor = ImageProcessor()
        
        # Process with memory profiling
        result = processor.process_image(
            test_img,
            str(self.output_dir),
            resize_percent=50,
            quality=85,
            enable_sharpening=True
        )
        
        return result
    
    def stress_test(self):
        """Stress test with extreme scenarios"""
        print("\n🔥 Running Stress Tests...")
        
        processor = ImageProcessor()
        stress_results = {}
        
        # Test 1: Very large image (8K resolution)
        print("\nTest 1: Processing 8K image...")
        large_img = Image.new('RGB', (7680, 4320))
        large_path = Path(self.temp_dir) / "8k_image.jpg"
        large_img.save(large_path, quality=95)
        
        start = time.time()
        result = processor.process_image(
            str(large_path),
            str(self.output_dir),
            resize_percent=25
        )
        stress_results['8k_image'] = {
            'time': time.time() - start,
            'success': result['success']
        }
        
        # Test 2: Rapid sequential processing
        print("\nTest 2: Rapid sequential processing (100 images)...")
        small_images = self.create_test_images(100, size=(500, 500))
        
        start = time.time()
        successes = 0
        for img in small_images:
            result = processor.process_image(
                img,
                str(self.output_dir),
                resize_percent=80
            )
            if result['success']:
                successes += 1
        
        stress_results['rapid_sequential'] = {
            'time': time.time() - start,
            'success_rate': successes / 100
        }
        
        # Test 3: Memory pressure test
        print("\nTest 3: Memory pressure test...")
        memory_images = []
        for i in range(20):
            img = Image.new('RGB', (3000, 3000))
            path = Path(self.temp_dir) / f"memory_test_{i}.jpg"
            img.save(path)
            memory_images.append(str(path))
        
        batch_processor = BatchProcessor()
        start = time.time()
        start_mem = psutil.Process().memory_info().rss / 1024 / 1024
        
        batch_processor.process_batch(
            memory_images,
            str(self.output_dir),
            resize_percent=50
        )
        
        end_mem = psutil.Process().memory_info().rss / 1024 / 1024
        stress_results['memory_pressure'] = {
            'time': time.time() - start,
            'memory_peak': end_mem - start_mem
        }
        
        self.results['stress_tests'] = stress_results
        return stress_results
    
    def generate_report(self):
        """Generate performance report"""
        print("\n" + "="*60)
        print("FOOTFIX PERFORMANCE REPORT")
        print("="*60)
        
        # Single image performance
        if self.results['single_image']:
            print("\n🖼  Single Image Processing:")
            print(f"  - Processing time: {self.results['single_image']['processing_time']:.2f}s")
            print(f"  - Memory used: {self.results['single_image']['memory_used']:.2f}MB")
        
        # Batch processing performance
        if self.results['batch_processing']:
            print("\n📦 Batch Processing Performance:")
            for size, metrics in self.results['batch_processing'].items():
                print(f"\n  Batch size {size}:")
                print(f"    - Total time: {metrics['total_time']:.2f}s")
                print(f"    - Per image: {metrics['time_per_image']:.2f}s")
                print(f"    - Memory used: {metrics['memory_used']:.2f}MB")
                print(f"    - Throughput: {size/metrics['total_time']:.2f} images/second")
        
        # Stress test results
        if 'stress_tests' in self.results:
            print("\n🔥 Stress Test Results:")
            stress = self.results['stress_tests']
            if '8k_image' in stress:
                print(f"  - 8K image processing: {stress['8k_image']['time']:.2f}s")
            if 'rapid_sequential' in stress:
                print(f"  - 100 rapid sequential: {stress['rapid_sequential']['time']:.2f}s")
                print(f"    Success rate: {stress['rapid_sequential']['success_rate']*100:.1f}%")
            if 'memory_pressure' in stress:
                print(f"  - Memory pressure test: {stress['memory_pressure']['memory_peak']:.2f}MB peak")
        
        # Performance recommendations
        print("\n💡 Performance Recommendations:")
        
        # Check single image performance
        if self.results['single_image']['processing_time'] > 5:
            print("  ⚠️  Single image processing is slow. Consider:")
            print("     - Optimizing image loading/saving")
            print("     - Using faster image libraries")
            print("     - Implementing GPU acceleration")
        
        # Check batch performance scaling
        if self.results['batch_processing']:
            sizes = sorted(self.results['batch_processing'].keys())
            if len(sizes) >= 2:
                scaling = (self.results['batch_processing'][sizes[-1]]['time_per_image'] / 
                          self.results['batch_processing'][sizes[0]]['time_per_image'])
                if scaling > 1.2:
                    print("  ⚠️  Poor batch scaling detected. Consider:")
                    print("     - Implementing parallel processing")
                    print("     - Optimizing memory allocation")
                    print("     - Using process pools for CPU-bound tasks")
        
        # Save detailed report
        report_path = Path(self.temp_dir).parent / "performance_report.txt"
        with open(report_path, 'w') as f:
            f.write("FOOTFIX PERFORMANCE REPORT\n")
            f.write("="*60 + "\n\n")
            f.write(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"System: {psutil.cpu_count()} CPUs, {psutil.virtual_memory().total/1024/1024/1024:.1f}GB RAM\n\n")
            
            import json
            f.write(json.dumps(self.results, indent=2))
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        return self.results
    
    def create_performance_graphs(self):
        """Create performance visualization graphs"""
        if not self.results['batch_processing']:
            return
        
        # Batch processing performance graph
        sizes = sorted(self.results['batch_processing'].keys())
        times = [self.results['batch_processing'][s]['total_time'] for s in sizes]
        per_image = [self.results['batch_processing'][s]['time_per_image'] for s in sizes]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Total time vs batch size
        ax1.plot(sizes, times, 'b-o', markersize=8)
        ax1.set_xlabel('Batch Size')
        ax1.set_ylabel('Total Time (seconds)')
        ax1.set_title('Batch Processing Time')
        ax1.grid(True, alpha=0.3)
        
        # Time per image vs batch size
        ax2.plot(sizes, per_image, 'r-o', markersize=8)
        ax2.set_xlabel('Batch Size')
        ax2.set_ylabel('Time per Image (seconds)')
        ax2.set_title('Processing Time per Image')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        graph_path = Path(self.temp_dir).parent / "performance_graphs.png"
        plt.savefig(graph_path, dpi=150)
        plt.close()
        
        print(f"\n📊 Performance graphs saved to: {graph_path}")


def run_performance_tests():
    """Run all performance tests"""
    tester = PerformanceTester()
    
    try:
        tester.setup()
        
        # Run tests
        tester.profile_single_image()
        tester.profile_batch_processing()
        tester.memory_profile_processing()
        tester.stress_test()
        
        # Generate report
        results = tester.generate_report()
        tester.create_performance_graphs()
        
        return results
        
    finally:
        tester.cleanup()


if __name__ == '__main__':
    print("🚀 Starting FootFix Performance Testing...")
    results = run_performance_tests()
    print("\n✅ Performance testing complete!")