"""
Interactive PocketFlow PostgreSQL Agent

Simple interactive version for user input.
"""

from agent import PostgreSQLAgent, DB_CONFIG


def main():
    """Interactive demo of the PocketFlow agent"""
    agent = PostgreSQLAgent(DB_CONFIG)
    
    print("Interactive PocketFlow PostgreSQL Agent (NL→SQL supported)")
    print("=" * 40)
    print("Enter natural language or SQL. Type 'exit' to quit.")
    print("=" * 40)
    
    while True:
        try:
            user_input = input("\nYour question or SQL: ").strip()
            
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
            elif not user_input:
                continue
            
            print("\nExecuting...")
            # Use NL→SQL path always; if it's SQL already, it will pass through
            result = agent.ask(user_input)
            print(f"\nResult:\n{result}")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
