#!/usr/bin/env python3
"""
Test script to verify Firestore connection
Run this to make sure Firestore is working before deploying
"""

try:
    from google.cloud import firestore
    
    print("🔧 Testing Firestore connection...")
    
    # Initialize Firestore client
    db = firestore.Client()
    
    # Test write
    test_doc = db.collection('test').document('connection_test')
    test_data = {'message': 'Hello Firestore!', 'timestamp': firestore.SERVER_TIMESTAMP}
    test_doc.set(test_data)
    print("✅ Write test successful")
    
    # Test read
    doc = test_doc.get()
    if doc.exists:
        print(f"✅ Read test successful: {doc.to_dict()['message']}")
    else:
        print("❌ Read test failed")
    
    # Clean up test document
    test_doc.delete()
    print("✅ Cleanup successful")
    
    print("🎉 Firestore is working correctly!")
    
except ImportError:
    print("❌ google-cloud-firestore not installed. Run: pip install google-cloud-firestore")
except Exception as e:
    print(f"❌ Firestore connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure you're authenticated with gcloud: gcloud auth application-default login")
    print("2. Make sure Firestore is enabled in your GCP project")
    print("3. Make sure your project has the Firestore API enabled")
