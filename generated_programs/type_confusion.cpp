#include <iostream>
#include <vector>
#include <string>
#include <memory>
#include <cstdint>

// Base class for all network packets
struct Packet {
    virtual ~Packet() = default;
};

// Login packet
struct LoginPacket : public Packet {
    std::string username;
    std::string password;
};

// Data packet containing raw bytes
struct DataPacket : public Packet {
    std::vector<uint8_t> payload;
};

// A connection handler that expects a specific sequence of packets
class ConnectionHandler {
public:
    void handlePacket(Packet* p) {
        // Vulnerability: The handler assumes the first packet is ALWAYS a LoginPacket
        // without verifying the type using dynamic_cast.
        // This is a type confusion vulnerability relying on incorrect state assumptions.

        if (!loggedIn) {
            // Unsafe downcast
            // We assume 'p' is a LoginPacket because we expect a login first.
            LoginPacket* login = static_cast<LoginPacket*>(p);

            std::cout << "[Server] Processing login attempt..." << std::endl;
            // Type Confusion Trigger:
            // If 'p' is actually a DataPacket, accessing 'username' interprets
            // the memory of DataPacket (e.g., the vector) as a std::string.
            std::cout << "  Username: " << login->username << std::endl;

            loggedIn = true;
        } else {
            // Similarly unsafe assumption, though less critical for this demo
            DataPacket* data = static_cast<DataPacket*>(p);
            std::cout << "[Server] Received data bytes: " << data->payload.size() << std::endl;
        }
    }

private:
    bool loggedIn = false;
};

int main() {
    ConnectionHandler handler;

    // Normal flow
    std::cout << "--- Normal Flow ---" << std::endl;
    {
        ConnectionHandler normalHandler;
        auto login = std::make_unique<LoginPacket>();
        login->username = "admin";
        normalHandler.handlePacket(login.get());

        auto data = std::make_unique<DataPacket>();
        data->payload = {0xDE, 0xAD, 0xBE, 0xEF};
        normalHandler.handlePacket(data.get());
    }

    // Exploit flow: Sending DataPacket when LoginPacket is expected
    std::cout << "\n--- Exploit Flow ---" << std::endl;
    {
        ConnectionHandler vulnerableHandler;

        auto maliciousData = std::make_unique<DataPacket>();
        // Fill payload with some data.
        // In many implementations, std::vector and std::string start with a pointer.
        // If we control the vector's data pointer, we might control where the string points.
        for(int i=0; i<8; i++) maliciousData->payload.push_back('A');

        std::cout << "Sending DataPacket (type confused as LoginPacket)..." << std::endl;

        // This triggers the type confusion
        // The program will likely crash or print garbage depending on memory layout/compiler.
        vulnerableHandler.handlePacket(maliciousData.get());
    }

    return 0;
}
