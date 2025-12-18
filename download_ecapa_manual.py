# download_ecapa_manual.py
# ONE-TIME SCRIPT — DOWNLOAD ECAPA-TDNN MODEL LOCALLY (OFFLINE READY)

from speechbrain.inference import SpeakerRecognition
import os

print("=" * 70)
print("DOWNLOADING ECAPA-TDNN MODEL TO LOCAL FOLDER (ONE TIME ONLY)")
print("=" * 70)
print("This will create:")
print("pretrained_models/spkrec-ecapa-voxceleb/")
print("   ├── embedding_model.ckpt (81MB)")
print("   ├── classifier.ckpt")
print("   ├── hyperparams.yaml")
print("   ├── label_encoder.ckpt")
print("   └── mean_var_norm_emb.ckpt")
print("=" * 70)

# Download and save directly to your project folder
model = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec-ecapa-voxceleb"
)

print("\n✅ ECAPA-TDNN MODEL DOWNLOADED SUCCESSFULLY!")
print("📁 Saved to: pretrained_models/spkrec-ecapa-voxceleb/")
print("🌍 You can now run your project OFFLINE forever")
print("🔒 No internet, no admin rights, no errors")
print("=" * 70)