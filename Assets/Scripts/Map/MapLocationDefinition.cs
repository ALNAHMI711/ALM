using System;
using UnityEngine;

namespace YOW.Map
{
    public enum LocationCategory
    {
        Bank, Fuel, Workshop, Restaurant, Mall, Hospital, Police, Market,
        WeaponShop, Service, House, Business, Airport, Port, Landmark
    }

    [Serializable]
    public sealed class MapLocationDefinition
    {
        public string id;
        public string displayName;
        public string region;
        public LocationCategory category;
        public Vector3 localPosition;
        public bool playerOwned;
        public string sponsorId;
    }
}
