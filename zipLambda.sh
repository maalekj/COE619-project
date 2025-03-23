#!/bin/bash

# Zip the files

# event files
zip record_event_lambda.zip record_event_lambda.py
zip get_event_lambda.zip get_event_lambda.py
zip get_all_events.zip get_all_events.py
zip update_event.zip update_event.py

# edge files
zip register_edge_point.zip register_edge_point.py
zip get_edge_node.zip get_edge_node.py
zip get_all_nodes.zip get_all_nodes.py
zip update_edge_node.zip update_edge_node.py
zip heartbeat.zip heartbeat.py

# Zip the contents of the event-evaluation folder
zip -r event_validate_lambda.zip event_validate_lambda/
