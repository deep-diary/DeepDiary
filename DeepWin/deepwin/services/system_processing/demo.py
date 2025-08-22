import argparse
from .manager import SystemManager

class SystemDemo:
    """系统信息处理演示类"""
    def __init__(self):
        self.manager = SystemManager()

    def test_hardware_info(self):
        """测试硬件信息获取"""
        print("\nTesting Hardware Information...")
        try:
            info = self.manager.get_specific_info('hardware')
            print("\nCPU Information:")
            print(f"  Processor: {info['cpu']['processor']}")
            print(f"  Cores: {info['cpu']['cores']}")
            print(f"  Threads: {info['cpu']['threads']}")
            print(f"  Frequency: {info['cpu']['frequency']:.2f} MHz")
            
            print("\nGPU Information:")
            print(f"  CUDA Available: {info['gpu']['available']}")
            if info['gpu']['available']:
                print(f"  Device Count: {info['gpu']['device_count']}")
                print(f"  Device Name: {info['gpu']['device_name']}")
                print(f"  CUDA Version: {info['gpu']['cuda_version']}")
            
            print("\nMemory Information:")
            print(f"  Total: {info['memory']['total'] / (1024**3):.2f} GB")
            print(f"  Available: {info['memory']['available'] / (1024**3):.2f} GB")
            print(f"  Usage: {info['memory']['percent']}%")
            
            return True
        except Exception as e:
            print(f"Hardware info test failed: {e}")
            return False

    def test_network_info(self):
        """测试网络信息获取"""
        print("\nTesting Network Information...")
        try:
            info = self.manager.get_specific_info('network')
            print(f"\nMAC Address: {info['mac']}")
            print(f"Hostname: {info['hostname']}")
            print(f"IP Address: {info['ip']}")
            
            if 'location' in info and isinstance(info['location'], dict):
                print("\nLocation Information:")
                print(f"  City: {info['location'].get('city')}")
                print(f"  Region: {info['location'].get('region')}")
                print(f"  Country: {info['location'].get('country')}")
                print(f"  Coordinates: {info['location'].get('lat')}, {info['location'].get('lon')}")
            
            return True
        except Exception as e:
            print(f"Network info test failed: {e}")
            return False

    def test_environment_info(self):
        """测试环境信息获取"""
        print("\nTesting Environment Information...")
        try:
            info = self.manager.get_specific_info('environment')
            print("\nOperating System Information:")
            print(f"  System: {info['os']['system']}")
            print(f"  Release: {info['os']['release']}")
            print(f"  Version: {info['os']['version']}")
            print(f"  Machine: {info['os']['machine']}")
            
            print("\nPython Information:")
            print(f"  Version: {info['python']['version']}")
            print(f"  Implementation: {info['python']['implementation']}")
            
            print("\nEnvironment Variables:")
            important_vars = ['PATH', 'PYTHONPATH', 'CUDA_PATH']
            for var in important_vars:
                if var in info['env_vars']:
                    print(f"  {var}: {info['env_vars'][var]}")
            
            return True
        except Exception as e:
            print(f"Environment info test failed: {e}")
            return False

    def test_all(self):
        """运行所有测试"""
        tests = [
            (self.test_hardware_info, "Hardware Information Test"),
            (self.test_network_info, "Network Information Test"),
            (self.test_environment_info, "Environment Information Test")
        ]
        
        results = []
        for test_func, test_name in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"Test {test_name} failed with error: {e}")
                results.append((test_name, False))

        print("\nTest Results:")
        for name, result in results:
            print(f"{name}: {'Success' if result else 'Failed'}")

        return all(result for _, result in results)

def main():
    parser = argparse.ArgumentParser(description='System Processing Demo')
    parser.add_argument('--test', 
                       choices=['hardware', 'network', 'environment', 'all'],
                       default='all', 
                       help='Test to run')
    
    args = parser.parse_args()
    demo = SystemDemo()
    
    test_funcs = {
        'hardware': demo.test_hardware_info,
        'network': demo.test_network_info,
        'environment': demo.test_environment_info,
        'all': demo.test_all
    }
    
    test_func = test_funcs.get(args.test)
    if test_func:
        test_func()
    else:
        print(f"Unknown test: {args.test}")

if __name__ == "__main__":
    main() 