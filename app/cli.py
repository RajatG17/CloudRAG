from app.graph.workflow import graph

def main():
    
    print("\nCloudRag Local Assistant")
    print("Type 'exit' to quit. \n")
    
    while True:
        
        question = input("Question: ").strip()
        
        if question.lower() in {"exit", "quit"}:
            break
        
        if not question:
            continue
        
        result = graph.invoke({
            "question": question
        })
        
        print("\nAnswer: ")
        print(result["answer"])
        
        print("\nRetrieved sources: ")
        
        for index, context in enumerate(
            result.get("contexts", []),
            start=1,
        ):
            print(
                f"[{index}] {context["source"]} (page {context["page"]})"
            )
        
        print("\n\n")
        
        metrics = result.get(
            "generation_metrics", 
            {}
        )
        
        if metrics:
            print("\nGeneration metrics")
            
            for key, val in metrics.items():
                print(f"{key}: {val}")
        

if __name__ == "__main__":
    main()