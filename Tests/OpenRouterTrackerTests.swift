import Foundation
import XCTest

// MARK: - Mock URL Protocol for Network Isolation
final class MockURLProtocol: URLProtocol {
    static var requestHandlers: [String: (URLRequest) throws -> (HTTPURLResponse, Data)] = [:]

    override class func canInit(with request: URLRequest) -> Bool {
        true
    }

    override class func canonicalRequest(for request: URLRequest) -> URLRequest {
        request
    }

    override func startLoading() {
        guard let url = request.url?.absoluteString,
              let handler = MockURLProtocol.requestHandlers.first(where: { url.contains($0.key) })?.value else {
            client?.urlProtocol(self, didFailWithError: URLError(.badURL))
            return
        }

        do {
            let (response, data) = try handler(request)
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: data)
            client?.urlProtocolDidFinishLoading(self)
        } catch {
            client?.urlProtocol(self, didFailWithError: error)
        }
    }

    override func stopLoading() {}
}

// MARK: - Model Tests
final class ModelTests: XCTestCase {
    func testTrackedKeyMaskingLongKey() {
        let key = "sk-or-v1-abcdef0123456789"
        let masked = TrackedKey.mask(key)
        XCTAssertEqual(masked, "sk-or-v1...6789")
    }

    func testTrackedKeyMaskingShortKey() {
        let key = "sk-short"
        let masked = TrackedKey.mask(key)
        XCTAssertEqual(masked, "••••••••")
    }

    func testTrackedKeyMaskingWithWhitespace() {
        let key = "   sk-or-v1-abcdef0123456789   \n"
        let masked = TrackedKey.mask(key)
        XCTAssertEqual(masked, "sk-or-v1...6789")
    }

    func testWidgetPayloadUsagePercent() {
        var payload = MockData.primaryPayload
        payload.keyLimit = 20.0
        payload.keyUsage = 10.0
        XCTAssertEqual(payload.usagePercent, 0.5, accuracy: 0.001)

        // Exceeding limit clamped to 1.0
        payload.keyUsage = 25.0
        XCTAssertEqual(payload.usagePercent, 1.0, accuracy: 0.001)

        // Nil limit returns 0.0
        payload.keyLimit = nil
        XCTAssertEqual(payload.usagePercent, 0.0)

        // Zero limit returns 0.0
        payload.keyLimit = 0.0
        XCTAssertEqual(payload.usagePercent, 0.0)
    }

    func testWidgetPayloadAccountBurnPercent() {
        var payload = MockData.primaryPayload
        payload.totalCredits = 200.0
        payload.totalUsage = 50.0
        XCTAssertEqual(payload.accountBurnPercent, 0.25, accuracy: 0.001)

        // Zero credits returns 0.0
        payload.totalCredits = 0.0
        XCTAssertEqual(payload.accountBurnPercent, 0.0)
    }

    func testDecodingOpenRouterKeyResponse() throws {
        let json = """
        {
            "data": {
                "label": "My Test Key",
                "usage": 12.34,
                "limit": 50.0,
                "is_free_tier": false,
                "usage_daily": 1.2,
                "usage_weekly": 5.4,
                "usage_monthly": 12.34
            }
        }
        """.data(using: .utf8)!

        let decoded = try JSONDecoder().decode(OpenRouterKeyResponse.self, from: json)
        XCTAssertEqual(decoded.data?.label, "My Test Key")
        XCTAssertEqual(decoded.data?.usage, 12.34)
        XCTAssertEqual(decoded.data?.limit, 50.0)
        XCTAssertEqual(decoded.data?.is_free_tier, false)
        XCTAssertEqual(decoded.data?.usage_daily, 1.2)
        XCTAssertEqual(decoded.data?.usage_weekly, 5.4)
        XCTAssertEqual(decoded.data?.usage_monthly, 12.34)
    }

    func testDecodingOpenRouterCreditsResponse() throws {
        let json = """
        {
            "data": {
                "total_credits": 100.50,
                "total_usage": 25.25
            }
        }
        """.data(using: .utf8)!

        let decoded = try JSONDecoder().decode(OpenRouterCreditsResponse.self, from: json)
        XCTAssertEqual(decoded.data?.total_credits, 100.50)
        XCTAssertEqual(decoded.data?.total_usage, 25.25)
    }
}

// MARK: - Storage Tests
final class StorageTests: XCTestCase {
    private var testDir: URL!

    override func setUp() {
        super.setUp()
        testDir = FileManager.default.temporaryDirectory.appendingPathComponent("OpenRouterTests_\(UUID().uuidString)")
        SharedStorage.customStorageDirectory = testDir
    }

    override func tearDown() {
        if let dir = testDir {
            try? FileManager.default.removeItem(at: dir)
        }
        SharedStorage.customStorageDirectory = nil
        super.tearDown()
    }

    func testAddUpdateDeleteKey() {
        let testLabel = "Unit Test Key \(UUID().uuidString.prefix(6))"
        let testApiKey = "sk-or-v1-test-key-1234567890abcdef"

        // 1. Add
        let added = SharedStorage.addKey(customLabel: testLabel, apiKey: testApiKey, isWidgetKey: false)
        XCTAssertEqual(added.customLabel, testLabel)

        let allKeys = SharedStorage.loadAllKeys()
        XCTAssertTrue(allKeys.contains(where: { $0.id == added.id }))

        // 2. Update
        var updated = added
        let updatedLabel = "\(testLabel) (Renamed)"
        updated.customLabel = updatedLabel
        SharedStorage.updateKey(updated)

        let reloadedKeys = SharedStorage.loadAllKeys()
        let found = reloadedKeys.first(where: { $0.id == added.id })
        XCTAssertEqual(found?.customLabel, updatedLabel)

        // 3. Delete
        SharedStorage.deleteKey(id: added.id)
        let keysAfterDelete = SharedStorage.loadAllKeys()
        XCTAssertFalse(keysAfterDelete.contains(where: { $0.id == added.id }))
    }

    func testSetWidgetKey() {
        let key1 = SharedStorage.addKey(customLabel: "K1", apiKey: "sk-or-v1-test11111111111", isWidgetKey: true)
        let key2 = SharedStorage.addKey(customLabel: "K2", apiKey: "sk-or-v1-test22222222222", isWidgetKey: false)

        SharedStorage.setWidgetKey(id: key2.id)

        let keys = SharedStorage.loadAllKeys()
        let reloadedKey1 = keys.first(where: { $0.id == key1.id })
        let reloadedKey2 = keys.first(where: { $0.id == key2.id })

        XCTAssertFalse(reloadedKey1?.isWidgetKey ?? true)
        XCTAssertTrue(reloadedKey2?.isWidgetKey ?? false)

        // Cleanup
        SharedStorage.deleteKey(id: key1.id)
        SharedStorage.deleteKey(id: key2.id)
    }

    func testPayloadCaching() {
        let testId = UUID()
        var payload = MockData.primaryPayload
        payload.customNickname = "Cached Nickname"

        SharedStorage.savePayload(payload, for: testId)
        let loaded = SharedStorage.getPayload(for: testId)

        XCTAssertNotNil(loaded)
        XCTAssertEqual(loaded?.customNickname, "Cached Nickname")
        XCTAssertEqual(loaded?.keyUsage, MockData.primaryPayload.keyUsage)
    }
}

// MARK: - Network Tests
final class NetworkServiceTests: XCTestCase {
    var session: URLSession!

    override func setUp() {
        super.setUp()
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [MockURLProtocol.self]
        session = URLSession(configuration: config)
        MockURLProtocol.requestHandlers = [:]
    }

    func testSuccessfulFetchData() async {
        let keyJson = """
        {
            "data": {
                "label": "Prod Server",
                "usage": 15.00,
                "limit": 30.00,
                "is_free_tier": false,
                "usage_daily": 2.50,
                "usage_weekly": 10.00,
                "usage_monthly": 15.00
            }
        }
        """.data(using: .utf8)!

        let creditsJson = """
        {
            "data": {
                "total_credits": 200.0,
                "total_usage": 50.0
            }
        }
        """.data(using: .utf8)!

        MockURLProtocol.requestHandlers["/api/v1/auth/key"] = { req in
            XCTAssertEqual(req.value(forHTTPHeaderField: "Authorization"), "Bearer sk-test-key")
            let response = HTTPURLResponse(url: req.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, keyJson)
        }

        MockURLProtocol.requestHandlers["/api/v1/credits"] = { req in
            let response = HTTPURLResponse(url: req.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, creditsJson)
        }

        let payload = await OpenRouterService.fetchData(
            apiKey: "sk-test-key",
            customNickname: "Prod Server",
            session: session
        )

        XCTAssertNil(payload.errorMessage)
        XCTAssertEqual(payload.keyUsage, 15.00)
        XCTAssertEqual(payload.keyLimit, 30.00)
        XCTAssertEqual(payload.keyRemaining, 15.00)
        XCTAssertEqual(payload.totalBalance, 150.00)
        XCTAssertEqual(payload.usageDaily, 2.50)
    }

    func testUnauthorizedFetchData() async {
        MockURLProtocol.requestHandlers["/api/v1/auth/key"] = { req in
            let response = HTTPURLResponse(url: req.url!, statusCode: 401, httpVersion: nil, headerFields: nil)!
            let data = "{\"error\": \"Unauthorized\"}".data(using: .utf8)!
            return (response, data)
        }

        let payload = await OpenRouterService.fetchData(
            apiKey: "invalid-key",
            customNickname: "Invalid",
            session: session
        )

        XCTAssertNotNil(payload.errorMessage)
        XCTAssertTrue(payload.errorMessage?.contains("Auth failed") ?? false)
    }
}

// MARK: - Main Test Runner Entrypoint
@main
struct TestRunner {
    static func main() {
        print("🧪 Running OpenRouter Tracker Test Suite...")
        let suite = XCTestSuite(name: "All Tests")
        suite.addTest(ModelTests.defaultTestSuite)
        suite.addTest(StorageTests.defaultTestSuite)
        suite.addTest(NetworkServiceTests.defaultTestSuite)

        let runner = TestObserver()
        XCTestObservationCenter.shared.addTestObserver(runner)
        suite.run()

        if runner.failedCount > 0 {
            print("❌ Test Run Failed: \(runner.failedCount) failures.")
            exit(1)
        } else {
            print("✅ All \(runner.testCount) tests passed successfully!")
            exit(0)
        }
    }
}

final class TestObserver: NSObject, XCTestObservation {
    var testCount = 0
    var failedCount = 0

    func testCaseDidFinish(_ testCase: XCTestCase) {
        testCount += 1
        let status = testCase.testRun?.hasSucceeded == true ? "PASSED" : "FAILED"
        if testCase.testRun?.hasSucceeded != true {
            failedCount += 1
        }
        print("  [\(status)] \(testCase.name)")
    }
}
