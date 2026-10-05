using System;
using UnityEngine;

namespace YOW.Save
{
    [Serializable]
    public sealed class SaveGame
    {
        public int schemaVersion = 1;
        public string playerId;
        public string selectedRegion = "Sana'a";
        public long money;
        public string[] ownedProperties = Array.Empty<string>();
        public string[] ownedVehicles = Array.Empty<string>();
        public string[] unlockedPacks = Array.Empty<string>();
    }

    public sealed class SaveGameService : MonoBehaviour
    {
        private const string SaveKey = "yow_save_v1";

        public void Save(SaveGame data)
        {
            PlayerPrefs.SetString(SaveKey, JsonUtility.ToJson(data));
            PlayerPrefs.Save();
        }

        public SaveGame Load()
        {
            if (!PlayerPrefs.HasKey(SaveKey))
                return new SaveGame();

            try { return JsonUtility.FromJson<SaveGame>(PlayerPrefs.GetString(SaveKey)); }
            catch { return new SaveGame(); }
        }
    }
}
