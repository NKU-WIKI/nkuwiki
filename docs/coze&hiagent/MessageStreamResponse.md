MessageStreamResponse:

event:<type>(text、image、audio、video、file,etc.)
data:data:{"event": <event_name>(message_start、message_end、knowledge_retrieve_start、knowledge_retrieve_end、qa_retrieve_start 、qa_retrieve_end,etc.)
            "docs":{(if event is knowledge_retrieve_end or qa_retrieve_end)
                "outputList":[
                    {
                        "output": string
                        ...
                    }
                ]
            }
            ...

        }
data:
data:
