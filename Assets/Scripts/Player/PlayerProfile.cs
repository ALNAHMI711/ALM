using System;
using UnityEngine;

namespace YOW.Player
{
    [Serializable]
    public sealed class PlayerProfile
    {
        public string playerId;
        public string displayName = "Player";
        public string region = "YE-SN";
        public string outfitId = "default";
    }

    public sealed class PlayerProfileComponent : MonoBehaviour
    {
        public PlayerProfile Profile { get; private set; } = new PlayerProfile();

        public void SetOutfit(string outfitId)
        {
            if (!string.IsNullOrWhiteSpace(outfitId))
                Profile.outfitId = outfitId;
        }
    }
}
