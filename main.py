from llama_index.utils.workflow import draw_all_possible_flows
from workflow import rag_workflow
from app import demo

if __name__ == "__main__":
    draw_all_possible_flows(rag_workflow, filename="workflow_vis.html")
    demo.launch(share=False)
