#!/bin/bash

# Zip the files
zip record_event_lambda.zip record_event_lambda.py
zip get_event_lambda.zip get_event_lambda.py
zip register_edge_point.zip register_edge_point.py

# Zip the contents of the event-evaluation folder
zip -r event_validate_lambda.zip event_validate_lambda/
