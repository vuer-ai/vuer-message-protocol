//! Basic message examples for VMP-RS
//!
//! Run with: cargo run --example basic_messages

use vmp_rs::prelude::*;
use serde_json::json;

fn main() -> Result<()> {
    println!("=== VMP-RS Basic Examples ===\n");

    // Example 1: Simple message
    println!("1. Creating a simple message:");
    let msg = Message::new("USER_CLICK")
        .with_value(json!({"x": 150, "y": 200}));
    println!("   Message: {:?}\n", msg);

    // Example 2: Serialize to MessagePack
    println!("2. Serializing to MessagePack:");
    let bytes = serialize_message(&msg)?;
    println!("   Serialized {} bytes", bytes.len());
    println!("   Note: MessagePack binary format is compact and efficient\n");

    // Example 3: Client event
    println!("3. Client event:");
    let client_event = ClientEvent::new(
        "CAMERA:main-camera:MOVE",
        json!({"position": [0.0, 1.5, -3.0]})
    );
    let bytes = serialize(&client_event)?;
    println!("   Serialized client event: {} bytes\n", bytes.len());

    // Example 4: Server event
    println!("4. Server event:");
    let server_event = ServerEvent::new(
        "SCENE:UPDATE",
        json!({"objects_count": 42})
    );
    let bytes = serialize(&server_event)?;
    println!("   Serialized server event: {} bytes\n", bytes.len());

    // Example 5: RPC request
    println!("5. RPC request:");
    let rpc_req = RpcRequest::new("render_frame", "rpc-12345")
        .with_args(vec![json!(100)])
        .with_kwargs({
            let mut map = std::collections::HashMap::new();
            map.insert("quality".to_string(), json!("high"));
            map.insert("format".to_string(), json!("png"));
            map
        });
    println!("   RPC etype: {}", rpc_req.etype);
    println!("   RPC rtype: {}\n", rpc_req.rtype);

    // Example 6: Component tree
    println!("6. Vuer component tree:");
    let sphere = VuerComponent::new("sphere")
        .with_prop("radius", json!(1.0))
        .with_prop("color", json!("#ff0000"))
        .with_prop("position", json!([0.0, 0.0, 0.0]));

    let box_comp = VuerComponent::new("box")
        .with_prop("size", json!([1.0, 1.0, 1.0]))
        .with_prop("color", json!("#00ff00"))
        .with_prop("position", json!([2.0, 0.0, 0.0]));

    let scene = VuerComponent::new("scene")
        .with_child(sphere)
        .with_child(box_comp)
        .with_prop("background", json!("#000000"));

    let bytes = serialize_component(&scene)?;
    println!("   Scene with {} children", scene.children.as_ref().unwrap().len());
    println!("   Serialized: {} bytes\n", bytes.len());

    // Example 7: ZData encoding
    println!("7. ZData custom type:");
    let zdata = ZData::new("custom.tensor")
        .with_binary(vec![1, 2, 3, 4, 5, 6, 7, 8])
        .with_dtype("float32")
        .with_shape(vec![2, 2])
        .with_field("device", json!("cuda:0"));

    let bytes = serialize(&zdata)?;
    println!("   ZData type: {}", zdata.ztype);
    println!("   Shape: {:?}", zdata.shape);
    println!("   Serialized: {} bytes\n", bytes.len());

    println!("=== All examples completed successfully! ===");
    Ok(())
}
