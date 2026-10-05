using System;
using UnityEngine;

namespace YOW.World
{
    [Serializable]
    public sealed class WorldRegion
    {
        public string id;
        public string displayName;
        public string countryCode = "YE";
        public Vector3 spawnPoint;
        public string contentPackId;
    }
}
