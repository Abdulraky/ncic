"""
Verify new database and test services
"""
from database import SessionLocal
from models import Official, EvidenceCollection, EvidenceItem
from services import PoliticianService, EvidenceService, AnalysisService

db = SessionLocal()

print("\n" + "=" * 60)
print("TESTING NEW DATABASE & SERVICES")
print("=" * 60)

# Test 1: Get all officials through service
print("\n[Test 1] PoliticianService.get_all_officials()")
officials = PoliticianService.get_all_officials(db)
print(f"✓ Retrieved {len(officials)} officials")
for official in officials:
    print(f"  - {official.name} ({official.official_id}) - {official.office}")

# Test 2: Get verified count
print("\n[Test 2] PoliticianService.get_verified_count()")
verified = PoliticianService.get_verified_count(db)
print(f"✓ {verified} verified officials")

# Test 3: Get with social media
print("\n[Test 3] PoliticianService.get_with_social_media_count()")
social = PoliticianService.get_with_social_media_count(db)
print(f"✓ {social} officials with social media")

# Test 4: Get unique counties
print("\n[Test 4] PoliticianService.get_unique_counties()")
counties = PoliticianService.get_unique_counties(db)
print(f"✓ {len(counties)} unique counties: {counties}")

# Test 5: Get all collections
print("\n[Test 5] EvidenceService.get_all_collections()")
collections = EvidenceService.get_all_collections(db)
print(f"✓ Retrieved {len(collections)} collections")
for collection in collections:
    print(f"  - {collection.official_name} (ID: {collection.id}) - {collection.status}")

# Test 6: Get items in first collection
if collections:
    print(f"\n[Test 6] EvidenceService.get_collection_items()")
    first_collection = collections[0]
    items = EvidenceService.get_collection_items(db, first_collection.id)
    print(f"✓ Collection {first_collection.id} has {len(items)} items")
    for item in items:
        print(f"  - {item.item_type}: {item.source_url[:60]}...")

# Test 7: Get stats
print(f"\n[Test 7] AnalysisService.get_results_summary()")
analysis_service = AnalysisService()
summary = analysis_service.get_results_summary(db)
print(f"✓ Verification results summary:")
for key, value in summary.items():
    print(f"  - {key}: {value}")

db.close()

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED")
print("=" * 60)
