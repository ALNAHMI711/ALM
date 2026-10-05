using System;
using UnityEngine;

namespace YOW.Ads
{
    [Serializable]
    public sealed class WorldAdDefinition
    {
        public string id;
        public string countryCode;
        public string region;
        public string placementId;
        public string advertiserName;
        public string headline;
        public string imageUrl;
        public string targetUrl;
        public bool enabled = true;
    }

    public sealed class WorldAdAnchor : MonoBehaviour
    {
        [SerializeField] private string placementId;
        public string PlacementId => placementId;
    }
}
