export function test(){
    console.log("Testas!!!")
}

export async function getData() {
    const url = "http://localhost:8002/elan-file/files/IG005.eaf";
    try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Response status: ${response.status}`);
        }
    
        const json = await response.json();
        return json;
    } catch (error) {
    
    }
}