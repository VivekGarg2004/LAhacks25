//@input SceneObject sphere
//@input Component.Camera camera
//@input float depth = 40

var transform = script.sphere.getTransform();
var initialPos = transform.getWorldPosition();
print("Script initialized for object interaction");

// For Spectacles touchpad
script.createEvent('TapEvent').bind(function (eventData) {
    print("Tap detected!");
    moveObject(0.5, 0.5); // Move to center on tap
});


// Standard touch events for preview
script.createEvent('TouchStartEvent').bind(function (eventData) {
    print("Touch detected!");
    moveObject(eventData.getTouchPosition().x, eventData.getTouchPosition().y);
});

// Add basic update event to check if script is running

function moveObject(x, y) {
    print("Moving object to screen position: " + x + ", " + y);
    var screenPos = vec2.create(x, y);
    var worldPos = script.camera.screenSpaceToWorldSpace(screenPos, script.depth);
    print("World position: " + worldPos.x + ", " + worldPos.y + ", " + worldPos.z);
    transform.setWorldPosition(worldPos);
}