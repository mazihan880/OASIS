#!/usr/bin/env python3
"""
Simple Test Script
Simplified test script - using standard OpenAI SDK for multi-turn tool calling
"""

import argparse
import os
from pathlib import Path

from evaluation import TestRunner


def main():
    parser = argparse.ArgumentParser(description="Simplified Agent Security Testing")
    parser.add_argument("--api-key", type=str, help="OpenAI API key")
    parser.add_argument("--base-url", type=str, help="Custom API base URL")
    parser.add_argument("--model", type=str, default="gpt-4", help="Model to use")
    parser.add_argument("--dataset", type=str, default="dataset.jsonl", help="Test dataset path")
    parser.add_argument("--tools-dir", type=str, default="tools", help="Tools directory")
    parser.add_argument("--mode", type=str, choices=["real_world", "direct_eval"], 
                       default="real_world", help="Test mode")
    parser.add_argument("--output-dir", type=str, default="./simple_test_results", help="Output directory")
    parser.add_argument("--max-tests", type=int, help="Maximum number of tests")
    parser.add_argument("--max-iterations", type=int, help="Maximum iterations (optional, default 10)")
    parser.add_argument("--test-level", type=str, help="Test level filter (0=L0, 1=L1, 2=L2, 3=L3, All=all levels, or list format like [0,2])")
    parser.add_argument("--max-workers", type=int, default=4,
                        help="Number of concurrent worker threads (1=sequential, >1=concurrent)")
    parser.add_argument("--temperature", type=float, default=0.6,
                        help="Model temperature parameter (0.0-2.0)")
    parser.add_argument("--timeout", type=int, default=1000,
                        help="Single request timeout (seconds)")
    parser.add_argument("--resume-from", type=str, help="Resume from specified trajectory directory")
    parser.add_argument("--difficulty", type=str, 
                        help="Difficulty filter (Low=low difficulty, Medium=medium difficulty, High=high difficulty, All=all difficulties, L0=all L0 data, or list format like [Low,High])")
    parser.add_argument("--retry-count", type=int, default=10,
                        help="Number of retries on failure, default 10")
    parser.add_argument("--thinking", action="store_true",
                        help="Enable thinking mode")
    
    args = parser.parse_args()
    
    # Get API key and URL
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    base_url = args.base_url or os.getenv("OPENAI_BASE_URL")
    
    if not api_key:
        print("❌ Please provide OpenAI API key (--api-key or set OPENAI_API_KEY environment variable)")
        return
    
    print("=" * 50)
    print(f"Model: {args.model}")
    if base_url:
        print(f"API URL: {base_url}")
    print(f"Mode: {args.mode}")
    print(f"Dataset: {args.dataset}")
    print(f"Output directory: {args.output_dir}")
    if args.max_tests:
        print(f"Max tests: {args.max_tests}")
    print()
    
    # Create test runner
    runner = TestRunner(
        api_key=args.api_key,
        model=args.model,
        output_dir=args.output_dir,
        max_iterations=args.max_iterations or 10,  # Default 10 iterations
        base_url=base_url,
        max_workers=args.max_workers,
        temperature=args.temperature,
        timeout=args.timeout,
        retry_count=args.retry_count,
        thinking=args.thinking
    )
    
    try:
        # Run tests
        results = runner.run_test_suite(
            dataset_path=args.dataset,
            tools_dir=args.tools_dir,
            mode=args.mode,
            max_tests=args.max_tests,
            test_level=args.test_level,
            difficulty=args.difficulty,
            resume_from=args.resume_from
        )
        
        # Calculate detailed metrics
        metrics = runner._calculate_detailed_metrics(results)
        
        print("\n" + "=" * 60)
        print("=" * 60)
        
        if metrics.get('overall'):
            overall = metrics['overall']
            print(f"Total tests: {overall['total_tests']}")
            print(f"Successful: {overall['successful_tests']}")
            print(f"Failed: {overall['failed_tests']}")
            print(f"Success rate: {overall['success_rate']:.1f}%")
            print(f"Average iterations: {overall['avg_iterations']:.1f}")
            print(f"Average tool calls: {overall['avg_tool_calls']:.1f}")
            print(f"Total execution time: {overall['total_execution_time']:.1f}s")
        
        # Display by level
        if metrics.get('by_level'):
            print("\n📈 Statistics by level:")
            for level, stats in metrics['by_level'].items():
                print(f"  {level}: {stats['success']}/{stats['total']} ({stats['success_rate']:.1f}%)")
        
        # Display by scenario type
        if metrics.get('by_harm_type'):
            print("\n🎭 Statistics by scenario type:")
            type_names = {"covert": "Covert", "explicit": "Explicit", "other": "Other"}
            for harm_type, stats in metrics['by_harm_type'].items():
                if stats['total'] > 0:
                    print(f"  {type_names.get(harm_type, harm_type)}: {stats['success']}/{stats['total']} ({stats['success_rate']:.1f}%)")
        
        print(f"\n📁 Results saved in: {args.output_dir}")
        print(f"📁 Trajectory files: {args.output_dir}/trajectories/")
        print(f"📄 Detailed summary: {args.output_dir}/summary_{runner.session_id}.json")
        
    except Exception as e:
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()