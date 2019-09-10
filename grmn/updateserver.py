# -*- coding: utf-8 -*-

from . import devices
from .proto import GetAllUnitSoftwareUpdates_pb2
from xml.dom.minidom import getDOMImplementation
import requests

PROTO_API_GETALLUNITSOFTWAREUPDATES_URL = "http://omt.garmin.com/Rce/ProtobufApi/SoftwareUpdateService/GetAllUnitSoftwareUpdates"
WEBUPDATER_SOFTWAREUPDATE_URL = "https://www.garmin.com/support/WUSoftwareUpdate.jsp"
GRMN_CLIENT_VERSION = "5.7.0.2"

class UpdateServer:

    def query_updates(self, sku_numbers):
        # Garmin Express Protobuf API
        device_xml = self.get_device_xml(sku_numbers)
        reply = self.get_unit_updates(device_xml)
        print(reply)

        # WebUpdater
        requests_xml = self.get_requests_xml(sku_numbers)
        reply = self.get_webupdater_softwareupdate(requests_xml)
        print(reply)

    def dom_add_text(self, doc, parent, elem_name, text):
        e = doc.createElement(elem_name)
        t = doc.createTextNode(text)
        e.appendChild(t)
        parent.appendChild(e)

    def get_device_xml(self, sku_numbers):
        dom = getDOMImplementation()
        doc = dom.createDocument(None, "Device", None)

        root = doc.documentElement

        root.setAttribute("xmlns", "http://www.garmin.com/xmlschemas/GarminDevice/v2")
        root.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.setAttribute("xsi:schemaLocation", "http://www.garmin.com/xmlschemas/GarminDevice/v2 http://www.garmin.com/xmlschemas/GarminDevicev2.xsd")

        model = doc.createElement("Model")
        self.dom_add_text(doc, model, "PartNumber", sku_numbers[0])
        self.dom_add_text(doc, model, "SoftwareVersion", "1")
        self.dom_add_text(doc, model, "Description", "-")
        root.appendChild(model)

        self.dom_add_text(doc, root, "Id", "2345678910")

        msm = doc.createElement("MassStorageMode")
        for sku in sku_numbers:
            uf = doc.createElement("UpdateFile")
            self.dom_add_text(doc, uf, "PartNumber", sku)
            v = doc.createElement("Version")
            self.dom_add_text(doc, v, "Major", "0")
            self.dom_add_text(doc, v, "Minor", "1")
            self.dom_add_text(doc, uf, "Path", "GARMIN")
            self.dom_add_text(doc, uf, "FileName", "GUPDATE.GCD")
            msm.appendChild(uf)
        root.appendChild(msm)

        xml = doc.toxml("utf-8")
        return xml

    def get_requests_xml(self, sku_numbers):
        dom = getDOMImplementation()
        doc = dom.createDocument(None, "Requests", None)
        doc.standalone = False

        root = doc.documentElement

        root.setAttribute("xmlns", "http://www.garmin.com/xmlschemas/UnitSoftwareUpdate/v3")

        for sku in sku_numbers:
            req = doc.createElement("Request")
            self.dom_add_text(doc, req, "PartNumber", sku)
            self.dom_add_text(doc, req, "TransferType", "USB")

            reg = doc.createElement("Region")
            self.dom_add_text(doc, reg, "RegionId", "14")

            ver = doc.createElement("Version")
            self.dom_add_text(doc, ver, "VersionMajor", "0")
            self.dom_add_text(doc, ver, "VersionMinor", "1")
            self.dom_add_text(doc, ver, "BuildType", "Release")

            reg.appendChild(ver)
            req.appendChild(reg)
            root.appendChild(req)

        xml = doc.toxml("utf-8")
        return xml

    def get_unit_updates(self, device_xml):
        query = GetAllUnitSoftwareUpdates_pb2.GetAllUnitSoftwareUpdates()
        query.client_data.client = "express"
        query.client_data.language ="en_US"
        query.client_data.client_platform = "Windows"
        query.client_data.client_platform_version = "601 Service Pack 1"
        query.device_xml = device_xml
        proto_msg = query.SerializeToString()

        headers = {
            "User-Agent": "Garmin Core Service Win - {}".format(GRMN_CLIENT_VERSION),
            "Garmin-Client-Name": "CoreService",
            "Garmin-Client-Version": GRMN_CLIENT_VERSION,
            "X-garmin-client-id": "EXPRESS",
            "Garmin-Client-Platform": "windows",
            "Garmin-Client-Platform-Version": "601",
            "Garmin-Client-Platform-Version-Revision": "1",
            "Content-Type": "application/octet-stream",
        }

        r = requests.post(PROTO_API_GETALLUNITSOFTWAREUPDATES_URL, headers=headers, data=proto_msg)

        if r.status_code != 200:
            r.raise_for_status()
            return None

        #print(r.content)
        with open("protoreply.bin", "wb") as f:
            f.write(r.content)
            f.close()

        reply = GetAllUnitSoftwareUpdates_pb2.GetAllUnitSoftwareUpdatesReply()
        reply.ParseFromString(r.content)

        return reply

    def get_webupdater_softwareupdate(self, requests_xml):
        headers = {
            "User-Agent": "Undefined agent",
        }

        data = {
            "req": requests_xml,
        }
        print(repr(data))
        r = requests.post(WEBUPDATER_SOFTWAREUPDATE_URL, headers=headers, data=data)

        if r.status_code != 200:
            r.raise_for_status()
            return None

        #print(r.content)
        with open("webupdaterreply.xml", "wb") as f:
            f.write(r.content)
            f.close()

        return r.content