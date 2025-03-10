
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
// export function compareStrings(strHyp, strRef) {
//     const wordsHyp = removeSymbols(strHyp).split(' ');
//     const wordsRef = removeSymbols(strRef).split(' ');
//     const result = [];

//     const maxLength = Math.max(wordsHyp.length, wordsRef.length);

//     for (let i = 0; i < maxLength; i++) {
//         if (!compareStringsCaseInsensitive(wordsHyp[i],wordsRef[i])) {
//             if (wordsHyp[i]) {
//                 result.push(`<span class="word-removed">${wordsHyp[i]}</span>`);
//             }
//             if (wordsRef[i]) {
//                 result.push(`<span class="word-added">${wordsRef[i]}</span>`);
//             }
//         } else {
//             result.push(wordsHyp[i]);
//         }
//     }
//     return result.join(' ');
// }

// export function compareStrings(str1, str2) {
//     const words1 = str1.split(/[,\s]+/);
//     const words2 = str2.split(/[,\s]+/);
//     const matrix = [];
//     const len1 = words1.length;
//     const len2 = words2.length;

//     // Initialize the matrix
//     for (let i = 0; i <= len1; i++) {
//         matrix[i] = [i];
//     }
//     for (let j = 0; j <= len2; j++) {
//         matrix[0][j] = j;
//     }

//     // Compute the Levenshtein distance
//     for (let i = 1; i <= len1; i++) {
//         for (let j = 1; j <= len2; j++) {
//             // const words1_i_1 = words1[i - 1];
//             // const words2_j_1 = words2[j - 1];
//             if (words1[i - 1] === words2[j - 1]) {
//                 matrix[i][j] = matrix[i - 1][j - 1];
//             } else {
//                 matrix[i][j] = Math.min(
//                     matrix[i - 1][j] + 1, // Deletion
//                     matrix[i][j - 1] + 1, // Insertion
//                     matrix[i - 1][j - 1] + 1 // Substitution
//                 );
//             }
//         }
//     }

//     // Backtrack to find the differences
//     let i = len1;
//     let j = len2;
//     const diff = [];
//     const diff2 = [];   
//     const levenshteinDistance = matrix[len1][len2];
//     const totalWords = Math.max(len1, len2);
//     const errorRate = (levenshteinDistance / totalWords) * 100;

//     while (i > 0 || j > 0) {
//         const words1_i_1 = words1[i - 1];
//         const words2_j_1 = words2[j - 1];
//         if (i > 0 && j > 0 && words1[i - 1] === words2[j - 1]) {
//             diff.unshift(words1[i - 1]);
//             diff2.unshift({"eq":words1[i - 1]});
//             i--;
//             j--;
//         } else if (j > 0 && (i === 0 || matrix[i][j - 1] < matrix[i - 1][j] && matrix[i][j - 1] < matrix[i - 1][j - 1])) {
//             diff.unshift(`<span class="word-added">${words2[j - 1]}</span>`);
//             diff2.unshift({"add":words2[j - 1]});
//             j--;
//         } else if (i > 0 && (j === 0 || matrix[i - 1][j] < matrix[i][j - 1] && matrix[i - 1][j] < matrix[i - 1][j - 1])) {
//             diff.unshift(`<span class="word-removed">${words1[i - 1]}</span>`);
//             diff2.unshift({"remove":words1[i - 1]});
//             i--;
//         } else {
//             diff.unshift(`<span class="word-substituted">(${words1[i - 1]}=>${words2[j - 1]})</span>`);
//             diff2.unshift({"sub":words1[i - 1], "by":words2[j - 1]});
//             i--;
//             j--;
//         }
//     }
//     diff.unshift(`<span>errorRate: ${Math.round(errorRate)}</span>`)
//     const addCount  = diff2.filter(e => e.add !== undefined).length
//     const removeCount  = diff2.filter(e => e.remove !== undefined).length
//     const subCount  = diff2.filter(e => e.sub !== undefined).length
//     console.log(`(${addCount}+${removeCount}+${subCount})/${totalWords}`);
    

//     return diff.join(' ');
// }

function mapDiffOp(diffOp){
    if(diffOp["op_eql"]){
        return diffOp["op_eql"];
    }else if(diffOp["op_ins"]){
        return `<span class="word-added">${diffOp["op_ins"]}</span>`;
    }else if(diffOp["op_sub"]){
        return `<span class="word-substituted">(${diffOp["op_sub"]} => ${diffOp["by"]})</span>`;
    }else if(diffOp["op_del"]){
        return `<span class="word-removed">${diffOp["op_del"]}</span>`;

    }
    return "Not mapped";
}

function renderDiffWords(word_distance){
    const diff= word_distance.map((x) =>  mapDiffOp(x))
    return diff.join(' ');
}



function get_time_details(segment, seg_type){
    const time_details=`${segment[seg_type+"_time_slot_start"]/1000}-${segment[seg_type+"_time_slot_end"]/1000}=${(segment[seg_type+"_time_slot_end"]+segment[seg_type+"_time_slot_start"])/1000}`
    return `<div class="time_details">(${time_details})</div>`
}

function get_text_details(segment, seg_type){
    const time_details=segment[seg_type+"_annotation_value"]
    return `<div class="text_details">(${time_details})</div>`
}

export function segmentToStr(segment, seg_type){
    if(!segment){
        return "-"
    }
    if(seg_type=="ref"){
        if(segment["ref_tier_local_id"]==null){
            return "-";
        }
        const time_details=get_time_details(segment, seg_type);
        const text_details=get_text_details(segment, seg_type);
        return ` ${segment["ref_tier_local_id"]} ${segment["ref_annot_local_id"]} ${time_details} ${text_details}`

    }else if(seg_type="hyp"){
        if(segment["hyp_tier_local_id"]==null){
            return "-";
        }
        const time_details=get_time_details(segment, seg_type)
        const text_details=get_text_details(segment, seg_type);
        return ` ${segment["hyp_tier_local_id"]} ${segment["hyp_annot_local_id"]} ${time_details} ${text_details}`
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
            // console.log(segment["word_op_stats"]["word_distance"]);
            const diffWords = renderDiffWords(segment["word_op_stats"]["word_distance"])
            
            additional_detail.push("("
                + diffWords +
        //     +compareStrings(segment["ref_annotation_value"],segment["hyp_annotation_value"])+
            ")")
        }
        return "==" + additional_detail.join(",");
    }
    return "-"
    
}