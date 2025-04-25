from flow import create_qa_flow

# Example main function
# Please replace this with your own main function
def main():
    shared = {
            "context": []
    }

    qa_flow = create_qa_flow()
    qa_flow.run(shared)

if __name__ == "__main__":
    main()
