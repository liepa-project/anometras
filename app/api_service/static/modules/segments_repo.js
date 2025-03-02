export function test(){
    console.log("Testas!!!")
}

export async function getSegmentsData(file_name) {
    const url = "http://localhost:8002/elan-file/files/"+file_name;
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

export async function getDiffData(file_name) {
    const url = `http://localhost:8002/elan-file/files/${file_name}/diff`;
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

export async function getFilesData(offset,limit) {
    console.log("[getFilesData]]", offset)
    const url = "http://localhost:8002/elan-file/files/record_types/org?limit="+limit+"&offset="+offset;
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

export function getFileName (str) {
    return str.split('\\').pop().split('/').pop();
}
