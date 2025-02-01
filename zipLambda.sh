#!/bin/bash

# Zip the files

# event files
zip record_event_lambda.zip record_event_lambda.py
zip get_event_lambda.zip get_event_lambda.py

# edge files
zip register_edge_point.zip register_edge_point.py
zip get_edge_node.zip get_edge_node.py

# Zip the contents of the event-evaluation folder
zip -r event_validate_lambda.zip event_validate_lambda/
