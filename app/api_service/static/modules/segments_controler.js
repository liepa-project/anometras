
function removeSymbols(inputString) {
    // Regular expression to match any non-alphanumeric character
    // const regex = /[^a-zA-Z0-9\s]/g;
    const regex = /[^\p{L}\p{N}\s]/gu;
    // Replace matched characters with an empty string
    const cleanedString = inputString.replace(regex, '');
    return cleanedString;
}

function compareStringsCaseInsensitive(str1, str2) {
    if(str1 == undefined && str2 != undefined){
        return false;
    }else if(str2 == undefined && str1 != undefined){
        return false;
    }else if(str2 == undefined && str1 == undefined){
        return true;
    }
    // Convert both strings to lowercase
    const lowerStr1 = str1.toLowerCase();
    const lowerStr2 = str2.toLowerCase();

    // Compare the lowercase strings
    return lowerStr1 === lowerStr2;
}

// Function to compare strings and highlight differences
export function compareStrings(strHyp, strRef) {
    const wordsHyp = removeSymbols(strHyp).split(' ');
    const wordsRef = removeSymbols(strRef).split(' ');
    const result = [];

    const maxLength = Math.max(wordsHyp.length, wordsRef.length);

    for (let i = 0; i < maxLength; i++) {
        if (!compareStringsCaseInsensitive(wordsHyp[i],wordsRef[i])) {
            if (wordsHyp[i]) {
                result.push(`<span class="removed">${wordsHyp[i]}</span>`);
            }
            if (wordsRef[i]) {
                result.push(`<span class="added">${wordsRef[i]}</span>`);
            }
        } else {
            result.push(wordsHyp[i]);
        }
    }
    return result.join(' ');
}


export function segmentToStr(segment, seg_type){
    if(!segment){
        return "-"
    }
    if(seg_type=="ref"){
        if(segment["ref_tier_local_id"]==null){
            return "-";
        }
        return ` ${segment["ref_tier_local_id"]} ${segment["ref_annot_local_id"]} (${segment["ref_time_slot_start"]/1000}-${segment["ref_time_slot_end"]/1000}=${(segment["ref_time_slot_end"]+segment["ref_time_slot_start"])/1000})`

    }else if(seg_type="hyp"){
        if(segment["hyp_tier_local_id"]==null){
            return "-";
        }
        return ` ${segment["hyp_tier_local_id"]} ${segment["hyp_annot_local_id"]} (${segment["hyp_time_slot_start"]/1000}-${segment["hyp_time_slot_end"]/1000}=${(segment["hyp_time_slot_end"]+segment["hyp_time_slot_start"])/1000})`
    }
    return "-";
    
}

export function operationToStr(seg_operation, segment){
    if(seg_operation=="noop"){
        return segment["ref_file_id"] + " - noop - "  + segment["hyp_file_id"];
    }else if(seg_operation=="ins"){
        return "+";
    }else if(seg_operation=="del"){
        return "-";
    }else if(seg_operation=="eql"){
        const start_changed=(segment["hyp_time_slot_start"]-segment["ref_time_slot_start"])/1000;
        const end_changed=(segment["hyp_time_slot_end"]-segment["ref_time_slot_end"])/1000;
        const annot_diff=segment["ref_annotation_value"] !== segment["hyp_annotation_value"];
        var additional_detail=[]
        if(start_changed!=0 || end_changed!=0 ){
             additional_detail.push(`(${start_changed};${end_changed})`);
        }
        if(annot_diff){
            additional_detail.push("("
            +compareStrings(segment["ref_annotation_value"],segment["hyp_annotation_value"])+
            ")")
        }
        return "==" + additional_detail.join(",");
    }
    return "-"
    
}