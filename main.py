from agent import run_agent

def main():
    print("=== Simple Safe Shopping Agent ===")
    print("Type 'exit' to quit.\n")

    role = input("Role (customer/admin): ").strip().lower()
    if role not in {"customer", "admin"}:
        print("Invalid role. Use 'customer' or 'admin'.")
        return

    while True:
        user_request = input("\nUser request: ").strip()
        if user_request.lower() == "exit":
            break
        if not user_request:
            continue

        result = run_agent(user_request, role)
        print("\nAgent:", result["answer"])

        if result.get("trace"):
            print("\n--- Tool Trace ---")
            for item in result["trace"]:
                print(item)

if __name__ == "__main__":
    main()
