import asyncio
import sys
from app.sync import SyncManager
from app.config import get_settings


async def main():
    settings = get_settings()
    sync_manager = SyncManager()
    
    try:
        await sync_manager.initialize()
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "register":
                if len(sys.argv) < 5:
                    print("Usage: python main.py register <username> <email> <password>")
                    return
                
                username = sys.argv[2]
                email = sys.argv[3]
                password = sys.argv[4]
                
                success = await sync_manager.register(username, email, password)
                if success:
                    print("Registration successful!")
                else:
                    print("Registration failed!")
            
            elif command == "login":
                if len(sys.argv) < 4:
                    print("Usage: python main.py login <username> <password>")
                    return
                
                username = sys.argv[2]
                password = sys.argv[3]
                
                success = await sync_manager.login(username, password)
                if success:
                    print("Login successful!")
                else:
                    print("Login failed!")
            
            elif command == "sync":
                if len(sys.argv) < 4:
                    print("Usage: python main.py sync <username> <password>")
                    return
                
                username = sys.argv[2]
                password = sys.argv[3]
                
                success = await sync_manager.login(username, password)
                if success:
                    await sync_manager.start_sync()
                    
                    try:
                        while True:
                            await asyncio.sleep(1)
                    except KeyboardInterrupt:
                        print("\nStopping sync...")
                        await sync_manager.stop_sync()
                else:
                    print("Login failed!")
            
            else:
                print(f"Unknown command: {command}")
                print("Available commands: register, login, sync")
        else:
            print("Usage: python main.py <command>")
            print("Commands:")
            print("  register <username> <email> <password>  - Register a new user")
            print("  login <username> <password>            - Login to the server")
            print("  sync <username> <password>             - Start file sync")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await sync_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
